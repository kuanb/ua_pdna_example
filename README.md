# Up and running via Docker
Navigate to the root directory of your cloned version of this repo. Typing `ls` should show you all files in the directory, including the `Dockerfile` for this repo. Run `docker build urbanaccess .` to create an image based off of this `Dockerfile`. Once complete, you can now create a container based off of this image.

TL;DR version: If you don't want to have a container that you can return to later and want to deal with any further steps with Docker, go ahead and run: `docker run --volume=$(pwd):/provisioning -it urbanaccess bash` at this point from the root directory of your copy of the Urban Access and repo and you're free to jump to the next section of this `README`.

Let's create a container and leave it running so that we can explore it's contents. To do this, run `docker run -d urbanaccess tail -f /dev/null` in your command line. Now, if you enter `docker ps`, you should be able to see that container listed as running. Under the `NAMES` section, you will see that the container has been given an arbitrary name. The container also has an alphanumeric `CONTAINER ID`. Copy that name and paste it in the following command: `docker rename [container_id] urbanaccess` where `container_id` is the copied alphanumeric id. Running `docker ps` will show you that the arbitrary name has been replaced with `urbanaccess`.

We can now open a bash shell in that Docker container via the following command: `docker exec -it urbanaccess bash`.

Recap of the steps we have taken so far:
```
docker build urbanaccess .
docker run -d urbanaccess tail -f /dev/null
docker rename [container_id] urbanaccess
docker exec -it urbanaccess bash
```

# Executing the script
Feel free to either run `examples/example.py` or follow along and enter in each step yourself to understand the steps involved in running through a typical UrbanAccess workflow. Entering `python` into the command prompt within the Docker container will drop you into a Python repl, which will enable you to walk through the `example.py` code step by step. You can do this by copying and pasting or, if you choose run the `example.py` script, it will move through each step and thenreturn a prompt (`y` or `N`) to ask whether you want to continue on to the next step if you want to follow along in a more "automated" manner.


# Using the Docker container while modifying the repo's codebase
If you intend on making modifications to the UrbanAccess code base, it helps to not have to rebuild the Docker image everytime the UA repo has a change to its codebase. In this situation, it is helpful to expose the Docker container in such a way that the container and your development share access to the a shared folder (the repo). In order to create an environment where the Docker container shares the repo with your standard development environment, run the following command: `docker run --volume=$(pwd):/provisioning -it {container_name} bash`. `--volume=$(pwd):/provisioning` will indicate that the current directory (you shoud be navigated to the UA repo's root directory), it a shared volume with the Docker container.