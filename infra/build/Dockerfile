# note: ➡️ In here, there is nothing. Think of it as a laptop you bought, but not even OS is installed.

# note: 🌎
# note: https://hub.docker.com/_/python
#
# note: 💬
# note: FROM is the base image. It is basically a "Docker file" another person created. Now you can "base" (that is why
# note: it is called a "base image"), your image on it.
#
# note: As you would guess, Python images give you a good starting point for your Python applications.
#
# note: 💬 We ALWAYS start with FROM and then give the image name and tag.
# note: By default, Docker looks 1st your machine and, 2nd to DockerHub.
#
# note: 💬 DockerHub is an "image repository". Think of it like Git for Docker Images.
# note: There are other image repositories available, but it always follows the same concepts/rules.
#
# note: 💬 Similar to git, we have an "image", which is "python" in this case. It is like the Repo in git.
# note: And we have "tag", which is like a branch in git. But the similarities end here.
#
# note: 💬 This is the syntax:
# note:     <image_name>:<tag>
FROM python:3.13-slim-trixie

# note: ➡️ In here, you have an operating system + whatever that has been added on top of it.
# note: For this image, that whatever is this:

# note: 🌎
# note:  https://github.com/docker-library/python/blob/668691664771c99b228c9acc107e9fec60b9bd96/3.13/slim-trixie/Dockerfile
# note: It has python installation and configuration, but also some useful tools like Make, and Wget

# note: 💬 Now we have something. We can actually run the docker image from here. Let's see

# note: 🏃‍♀️ docker build . -t nova -f infra/build/Dockerfile --no-cache

# note: 💬 When we "build" it, it creates an image from the instructions of this Dockerfile. Dockerfile is basically it.
# note: It is Docker specific instructions/commands for building Docker images.

# note: 👀 Check the stages runnning in CLI

RUN apt-get update
RUN echo "hello world" > hello_world.txt

# note: ➡️ In here, we ran a command while building the image. It is just like how we would run in CLI, but at the image
# note: creation. The results of it (e.g. modifications to the "machine"), is "baked" or "kept" in the image.

# note: 💬 With RUN, you can execute any CLI command. We use it to prepare our images for when we will run our app.
# note: The syntax is simple. "RUN <and single-line command>". Let's see what that echo did.

# note: 🏃‍♀️  docker run nova

# note: 👀 Well.. Nothing happened there visually. But in the background, it started a container for the Docker image,
# note: we created and did what has been asked to do when it is started: which is nothing. Then it finished its
# note: job of doing... nothing, and it stopped.

# note: 📇 Image: the "abstract"/"blueprint".  Container: the "concrete"/"running"/"instance" of an image.

# note: 💬 Now let's give it a more interesting thing. Let's make it print the hello_world.txt we created in the image.
# note: Remember! That file created will be in the container when it started.

# note: 🏃‍  docker run nova cat /hello_world.txt

RUN apt-get install openjdk-21-jdk --yes

WORKDIR /nova

# note: ➡️ In here, we changed (1) the directory we are building this image, and (2) set the directory of when the container
# note: will start at. You can see it easily with a simple docker run.

# note: 💬 By default, the starting point of a container is "/" for Linux. Unless the base image has not change it ofc.

# note: 🏃 docker run nova pwd

COPY requirements.txt .

# note: ➡️ In here, we ask Docker to copy a file from our local, to the image. For sure we do not want to hard-code our
# note: files inside this Dockerfile!

# note: 💬 The syntax and way of working is pretty simple:
# note: COPY <path_to_file_in_local> <path_to_file_you_want_it_in_the_image>

# note: 💬 Mind that "for the image", we are at /nova dir now! So it will copy from requirements.txt to /nova/requirements.txt
# note: Let's see!

# note: 💬 Another important note is to remember the docker build "bakes" files in the image. It means that
# note: (if you are not using volumes - which we will not do this week) if you change a file (in your local)
# note: the docker image will not be updated. If you change a file that you copy, you will need to build the
# note: docker image again.
# note: This is a simple thing... but the root of many "bugs". I have spent so much time debugging only to
# note: realize I forgot to rebuild the image... 🤦‍♂️

# note: 🏃 docker run nova head requirements.txt


RUN pip install -r requirements.txt

ENV PYTHONPATH=/nova/

# note: ➡️ In here, we put an OS Env variable to the image.

# note: 💬 Instead of using export, we use this. Why? Because export is not persisting the command. It is just for the
# note: current session.

COPY src/ src/
COPY configs/ configs/
COPY data/trx/ data/trx/
COPY models/.placeholder models/.placeholder

# note: ➡️ In here, you have a full image!

# note: ⚠️ Remember! Because we did not set any command to run when container is started, without giving it a command
# note: to run, it will just start and stop.

# note: 📚 Continue at --> Readme.md --> ## Where is my image?