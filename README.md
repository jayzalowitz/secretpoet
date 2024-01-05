# secretpoet


This is an application that allows deployment of a blog that works with the mobilecoin system to publish secret messages

normal operation steps
get docker
run docker engine for your desktop
run sh up.sh


to deploy on aws, I have added a infra.tf, which after setting up terraform should work out of the box.
Note, that I currently use my own local docker copy of what im working on to push it there, so you will need to adjust the terraform script to include your own instead of this
image = "jayzalowitz/secretpoetweb", # Replace with your actual image
deploying your own docker image can be done multiple ways, but is really easy so i suggest just googling