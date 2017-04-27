import geopandas as gpd
import pandana as pdna
import pandas as pd
import shapely.wkt
import sys
import urbanaccess

# sets whether 'interactive mode' is on
CONTINUECHECKON = False

# decide whether or not to plot the network from UA
PLOT_NETWORK = False

long_dash = ''.join(['-' for n in range(25)])
def continue_check(custom_note='', clarify=False):
    for item in ['\n', long_dash, custom_note]:
        print(item)
    
    # don't proceed unless check bool is on
    if not CONTINUECHECKON:
        return None
    
    message = '[yN] Continue? '
    if clarify:
        message = 'Not a valid option. Try again.\n' + message
    response = raw_input(message)
    if response in ['y', 'Y']:
        print(long_dash)
    elif response in ['n', 'N']:
        print('Exiting...')
        sys.exit()
    else:
        clarify = True
        continue_check(custom_note, clarify)


# let's find transit providers in Madison, WI
search_results = urbanaccess.gtfsfeeds.search(search_text='madison')
# 4 results will be returned, you can see them by printing the dataframe below
print('Results from searching for Madison on now-defunct GTFS Data Exchange')
print(search_results.head(5))

# =============
# Section break
# =============
continue_check(('We just queried for transit providers with UA. '
                'Next, we will specify a transit resource to download.'))

# add a feed to the gtfs to include in the analysis
feeds = urbanaccess.gtfsfeeds.feeds
name = 'madison'
# Note: query suggests: http://www.cityofmadison.com/metro/gtfs/mmt_gtfs.zip
#       but this address is currently is 404'ing (04-16-2017)
#       ...as a result, using link below which _does_ work in the meantime
url = 'http://www.gtfs-data-exchange.com/agency/city-of-madison/latest.zip'
new_feed =  {name:url}
feeds.add_feed(new_feed)

# download the feed, will be placed in folders within data/gtfsfeed_text
# according to the dict key name
urbanaccess.gtfsfeeds.download()

# =============
# Section break
# =============
continue_check(('Next, we need to load the feeds into a Pandas DataFrame.'))

# now that we have saved the raw gtfs data, we need to load it in
gtfsfeed_path = None # use default gtfs save location
validation = True
verbose = True
bbox = (-89.566399, 42.984056, -89.229584, 43.171917)
remove_stops_outsidebbox = True
append_definitions = True
# updates these attributes: stops, routes, trips, stop_times, calendar,
#                           calendar_dates, stop_times_int, headways
loaded_feeds = urbanaccess.gtfs.load.gtfsfeed_to_df(gtfsfeed_path,
                                                    validation,
                                                    verbose,
                                                    bbox,
                                                    remove_stops_outsidebbox,
                                                    append_definitions)
# =============
# Section break
# =============
continue_check(('Next, we need to interpolate stop times data from GTFS.'))

# what remains an empty dataframe is stop_times_int, which we still
# need to generate before we can get to calculating headways
columns = ['route_id', 'direction_id', 'trip_id', 'service_id', 
           'unique_agency_id']
day = 'wednesday' # pick an arbitrary day of week
tripschedualselector = urbanaccess.gtfs.network.tripschedualselector
cal_selected_trips = tripschedualselector(
                                input_trips_df = loaded_feeds.trips[columns],
                                input_calendar_df = loaded_feeds.calendar,
                                day = day)

# approximate missing stop times via linear interpolation
interpolatestoptimes = urbanaccess.gtfs.network.interpolatestoptimes
intermediate_interpolation = interpolatestoptimes(
                                stop_times_df = loaded_feeds.stop_times,
                                calendar_selected_trips_df = cal_selected_trips,
                                day = day)

# now calculate the difference in top times in new column
timedifference = urbanaccess.gtfs.network.timedifference
stop_times_int = timedifference(stop_times_df = intermediate_interpolation)

# now we can update loaded_feeds with this new dataframe
loaded_feeds.stop_times_int = stop_times_int

# =============
# Section break
# =============
continue_check(('Now we can calculate headways with the interpolated data.'))

# now we need to calculate the headways, given the downloaded gtfs
headway_timerange = ['07:00:00','10:00:00'] # approx a.m. peak
# the below function updates loaded_feeds, so that headways is populated
loaded_feeds = urbanaccess.gtfs.headways.headways(
                    loaded_feeds, headway_timerange)

# =============
# Section break
# =============
continue_check(('At this point we are able to save/reload the data locally.'))

# save the results from these initial processing steps locally
filename = 'temp_network_analyzed.h5'
urbanaccess.gtfs.network.save_processed_gtfs_data(loaded_feeds, 'data', filename)
# we can now reload from that save location if we want
loaded_feeds = urbanaccess.gtfs.network.load_processed_gtfs_data('data', filename)

# =============
# Section break
# =============
continue_check(('Next, we need to generate the transit and osm networks.'))

# to proceed, we need to generate a network describing the transit data
ua_network = urbanaccess.gtfs.network.create_transit_net(
                                gtfsfeeds_df = loaded_feeds,
                                day = day,
                                timerange = headway_timerange,
                                overwrite_existing_stop_times_int = False,
                                use_existing_stop_times_int = True,
                                save_processed_gtfs = False)

# now we're ready to download OSM data, let's use same bbox from gtfs search
osm_nodes, osm_edges = urbanaccess.osm.load.ua_network_from_bbox(bbox = bbox)

# with the osm data, we can create a network just as we did with the gtfs data
ua_network = urbanaccess.osm.network.create_osm_net(
                                osm_edges = osm_edges,
                                osm_nodes = osm_nodes,
                                travel_speed_mph = 3, # walk speed average
                                network_type = 'walk')
# =============
# Section break
# =============
continue_check(('Now we have all networks we need, so we can integrate them.'))

# result urbanaccess_nw variables is an object with the following attributes:
#   osm_edges, osm_nodes,
#   transit_edges, transit_nodes
# and then returns the above, plus:
#   net_connector_edges, net_edges, net_nodes
urbanaccess_nw = urbanaccess.network.integrate_network(
                                urbanaccess_network = ua_network,
                                headways = True,
                                urbanaccess_gtfsfeeds_df = loaded_feeds,
                                headway_statistic = 'mean')

color_range = urbanaccess.plot.col_colors(
                        df=urbanaccess_nw.net_edges,
                        col='mean',
                        num_bins=5,
                        cmap='YlOrRd',
                        start=0.1,
                        stop=0.9)

if PLOT_NETWORK:
    urbanaccess.plot.plot_net(
                        nodes=urbanaccess_nw.net_nodes,
                        edges=urbanaccess_nw.net_edges,
                        x_col='x',
                        y_col='y',
                        bbox=bbox,
                        fig_height=25,
                        margin=0.02,
                        edge_color=color_range,
                        edge_linewidth=1,
                        edge_alpha=1,
                        node_color='black',
                        node_size=1,
                        node_alpha=1,
                        node_edgecolor='none',
                        node_zorder=3,
                        nodes_only=False)

# now to shift over to pandana's domain
nod_x = urbanaccess_nw.net_nodes['x']
nod_y = urbanaccess_nw.net_nodes['y']
edg_fr = urbanaccess_nw.net_edges['from']
edg_to = urbanaccess_nw.net_edges['to']
edg_wt_df = urbanaccess_nw.net_edges[['weight']]

# insantiate a pandana network object
p_net = pdna.Network(nod_x, nod_y, edg_fr, edg_to, edg_wt_df)

# precompute step, requires a max 'horizon' distance
horizon_dist = 60
p_net.precompute(horizon_dist)

# read in an example dataset
blocks_df = pd.read_csv('./data/blocks.csv')
geometry = blocks_df['geometry'].map(_parse_wkt)
blocks_df = blocks_df.drop('geometry', axis=1)
crs = {'init': 'epsg:4326'}
blocks_gdf = gpd.GeoDataFrame(blocks_df, crs=crs, geometry=geometry)

# we need to extract the point lat/lon values
blocks_gdf['x'] = blocks_gdf.centroid.map(lambda p: p.x)
blocks_gdf['y'] = blocks_gdf.centroid.map(lambda p: p.y)

#  set node_ids as an attribute on the geodataframe
blocks_gdf['node_ids'] = p_net.get_node_ids(blocks_gdf['x'], blocks_gdf['y'])
p_net.set(blocks_gdf['node_ids'],
          variable=blocks_gdf['emp'],
          name='emp')

# This results in near-identical series outputs
# Expected result would be greater job access each iteration (higher n)
for n in [15,30,45,60]:
    s = p_net.aggregate(n, type='sum', decay='linear', imp_name='weight', name='emp')
    print(s.max())
    print(s.mean())
    print(s.min())
    print(len(s[s>0]))

p_net.plot(s, 
         bbox=bbox,
         fig_kwargs={'figsize': [35, 35]},
         bmap_kwargs={'suppress_ticks': False,
                      'resolution': 'h', 'epsg': '26943'},
         plot_kwargs={'cmap': 'BrBG', 's': 8, 'edgecolor': 'none'})

# helper functions
def _parse_wkt(s):
    """Parse wkt and ewkt strings into shapely shapes.

    For ewkt (the PostGIS extension to wkt), the SRID indicator is removed.
    """
    if s.startswith('SRID'):
        s = s[s.index(';') + 1:]
    return shapely.wkt.loads(s)
