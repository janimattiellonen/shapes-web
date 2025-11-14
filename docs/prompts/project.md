#Project description

A web app that allows the user to upload an image and detect whether the image contains an ellipse, a rectangle, a triangle or neither of these three.

##Starting point

I already have a keras model for detecting ellipses, rectangles and triangles. However, it is used by calling command line scripts written in python.

This existing project is located in /Users/janimattiellonen/Documents/Development/Keras/Shapes. Open README.md to learn more about this project's setup. This information is provided as a context, and not relevant at the


##Web app

##Location

The new web app is to be created in /Users/janimattiellonen/Documents/Development/Keras/shapes-web


###Architecture

The web app should be split into a simple React frontend for uploading the image and returning the result and a Python based backend for processing the uploaded image.

####Frontend

- React 19
- Vite.js framework
- Typescript


####Backend

- FastAPI
- create a Docker environment (docker-compose.yml) for contained environment
