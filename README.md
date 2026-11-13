# uva-mlprod-code
## Week 3 - Containerization

# Creating a Dockerfile

For the same of simplicity, you can consider a Docker image as the definition of a container, or the template of it.
Using the image, you can start/create many instances of it. It is like the cookie-cutter. You use it to create as many
cookies as you want.

In order to create an image, we need to create and implement a `Dockerfile`. This single file will hold all the 
implementation regarding our container. From which OS we will be using, to what to run inside it when we start the 
container.


## Create a Dockerfile

We will go ahead and create a Dockerfile. It is really just called `Dockerfile`:

`touch Dockerfile`

Now let's go ahead and start implementing.

## Building a Docker Image

We have defined our Dockerfile, which is a series (for now a single) of Docker commands that creates our container. 
Now, let's actually build an image using the definition. Building in Docker context is similar to compiling in
programming languages. Docker engine will take the Docker file, and create an image out of the instructions.

We build a Docker image using `docker build` command. It is a good idea to study what it does and options through
`docker build --help`

Let's study the command:

`docker build --file Dockerfile .`

The help command will help us with understanding it:

```shell
kemalty@DESKTOP-E2PGG9L:~/uva-mlprod-code/deploying-ml-systems/0-containerization/0-creating-img$ docker build --help
Start a build

Usage:  docker buildx build [OPTIONS] PATH | URL | -

Start a build

Aliases:
  docker build, docker builder build, docker image build, docker buildx b

Options:
# ...
  -f, --file string                   Name of the Dockerfile (default: "PATH/Dockerfile")
      --iidfile string                Write the image ID to a file
      --label stringArray             Set metadata for an image
      --load                          Shorthand for "--output=type=docker"
      --metadata-file string          Write build result metadata to a file
      --network string                Set the networking mode for the "RUN" instructions during build
                                      (default "default")
      --no-cache                      Do not use cache when building the image
      --no-cache-filter stringArray   Do not cache specified stages
# ...
  -t, --tag stringArray               Name and optionally a tag (format: "name:tag")
      --target string                 Set the target build stage to build
      --ulimit ulimit                 Ulimit options (default [])

Experimental commands and flags are hidden. Set BUILDX_EXPERIMENTAL=1 to show them.
```

## Where is my image?

So we built the image. But where is it?!?!  

When you build an image, it is stored on your local. You cannot find it in any path though. Docker stores it inside
of its installation in a binary file. You can check the images that exists in your local via:

`docker image ls`

You can see the images exists in you local with details using this command.

```shell
(.venv) ➜  uva-mlprod-code git:(v2/w4-containerization) ✗ docker image ls
REPOSITORY                TAG        IMAGE ID       CREATED             SIZE
nova                      latest     32c46b9f5358   20 minutes ago      4.46GB
```

Looks like there is an image there indeed.

### Repo and Tag's

Docker identifies a specific image with two factors:

Repo: The collection of images for the specific purpose. Think like a project.
Tag: The version of an image in a particular repo. Think like a version. Mind that there is no guarantee that the tag's
will be similar.

Now if you look at Python repo in the Docker hub, you will see many many tags: 

https://hub.docker.com/_/python/

The tag we used as our base image is the `3.13-slim-bullseye`:

https://hub.docker.com/layers/library/python/3.13-slim-bullseye/images/sha256-359640afda390082050309c076a65af6b597572cae0d266a2a46f2a164e16e57

In Docker, we use the following naming for images:

`<REPO>:<TAG>`

Now let's build our image again, but this time use a tag.

__Tip: use `docker image prune` to clean up un-tagged images on your local__

How do we use tags? Well, let's look at the help command:

```shell
kemalty@DESKTOP-E2PGG9L:~/uva-mlprod-code/deploying-ml-systems/0-containerization/0-creating-img$ docker build --help
Usage:  docker buildx build [OPTIONS] PATH | URL | -
# ...
  -t, --tag stringArray               Name and optionally a tag (format: "name:tag")
      --target string                 Set the target build stage to build
      --ulimit ulimit                 Ulimit options (default [])
```

### The `latest` tag

If you read carefully, the help command offers this info:

```shell
  -t, --tag stringArray               Name and optionally a tag (format: "name:tag")
```

It states "optionally a tag". So a tag is actually optional. When you do not provide a tag, it automatically becomes
`latest`.

```shell
kemalty@DESKTOP-E2PGG9L:~/uva-mlprod-code/deploying-ml-systems/0-containerization/0-creating-img$ build . -t nova:0.1 -f infra/build/Dockerfile
```

Neat! One last thing to worry about... Well actually not... There are a few reasons but the main one is to prevent
version confusion.


### Layers

A lot has happened on your command line, right? Well, here is a light explanation of what happened:

` =>  CACHED [1/2] FROM docker.io/library/python:3.13-slim-bullseye@sha256:631af3fee9d0b0a046855a62af745c1 0.0s`

In this step (1 out of 2), Docker (did not) downloaded that base image you defined from the internet. It is nice that
Docker provides this service free and public.

In this case you can see the `CACHED` pre-fix and it took 0.0 second. It is because I already had that layer in 
my local, so instead of downloading it, Docker engine just reused it.

` =>  [2/2] RUN apt-get update                                                                             10.8s`                                                                  4.5s`

In this second step, Docker ran that command (`apt-get update`) inside the image and prepared it. So your image
just got updated and saved like that.

But how about this?

` => => exporting layers                                                                           0.1s`

Well, Docker is very smart! It works by layers. It means that, each step above created a layer. Layers sit on top of
each other. Why is that smart? Because, for instance, if you change the file you copied, you dont have to execute the
first two steps/layers! This saves a lot of time as some images/containers can get pretty big and slow to build. That is
also why it is a good idea to layer down your container as you build it. So do not write one big `RUN` but try to
distribute it :) 


## ENV

Configuring your application with environment variables is not only a neat idea, a best practice. It allows you to
automatically and easily setup your app for different environments (and markets) without touching the application code. 
It is one of the topics that 12-factor app discusses (https://12factor.net/config).

The way to setup environments in Docker is via `ENV` command. You can use it as follows:

`ENV <var_name>=<var_value>`

e.g. `ENV STAGE=PROD`

Configuring our apps via environment variables offers us a great deal of ease when we want to deploy our app in different
environments (e.g. staging vs production).


## Checking Containers Running in Local

In order to see which containers are running, we can use the command:

`docker ps`

This will list all the containers that are running in our machine. 


## Stopping a Container

There are some occasions that will stop a container:

0. The process(es) you are running complete(s).
1. User stops the container
2. A process (e.g. Python code running) crashes
3. The host machine is having an issue and/or stopped (e.g. running our of resources)

Since our machine is healthy, and the process is not crashing, and it will never finish, it means that the container
will keep running unless we (the user) stops it. In order to stop a container, we use the command below:

`docker stop <container_id>`

Mind that we are using the container id and not the image name. It is due to that image is a template of a container,
and with that template, we can run many many containers. In the same machine, or in different machines.

Let's go ahead and stop the container now. In my machine now, the container id is  `7883de17b1c4`. If I start a container
again, it will probably be a different id.


## Debug a container

One of the most useful skill to have is being able to debug a container, or what is going on inside of it. The most simple
way to debugging an image or a container is to "get inside" of the container. We achieve this by executing the `bin/bash`
inside the container and running it interactive.

`bin/bash` is the most popular shell, and interactive means that the input and output flow through your terminal. In
order to execute it, we use the following command:

`docker run -it <image_name> /bin/bash`

This will create a container and run a shell in it. Go ahead and try it!

`docker run -it nova:0.3 bin/bash`

Well, what happened? You started to get the output of our app right? It is because the command defined with `ENTRYPOINT`
got executed first, and then it gave you an interactive session. You are still inside of the container, but the python
app is running in the same process. Now that you are actually "inside the container", you can kill the python app by 
CMD+C.

It is great that we can get inside of the container. But how are we gonna debug the container when that python app
is running and blocking the process? This is a good time to tell you that there is another docker command that is useful.
The `docker exec <container_id> <command_to_run>` executes given command inside a running container. Let's give it a try.

Let's now try to get an interactive shell inside the container. I can do what we did with docker run:

`docker exec -it 5a3e2eaebb99 bin/bash`

Yay! Now we are inside the container with an interactive shell, and we can do anything in the container!
