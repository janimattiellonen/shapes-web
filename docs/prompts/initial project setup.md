#Project description

A web app that allows the user to upload an image and detect whether the image contains an ellipse, a rectangle, a triangle or neither of these three.


##Web app

Before implementaing any shape detection or file upload, I need a frontend and a backend set up and running.


##Location

The new web app is to be created in /Users/janimattiellonen/Documents/Development/Keras/shapes-web


###Architecture

The web app should be split into a simple React frontend for uploading the image and returning the result and a Python based backend for processing the uploaded image.

####Frontend

- React 19
- Vite.js framework
- Typescript

Create the Vite project in /Users/janimattiellonen/Documents/Development/Keras/shapes-web/frontend


####Backend

- FastAPI
- create a Docker environment (docker-compose.yml) for contained environment

Create the Vite project in /Users/janimattiellonen/Documents/Development/Keras/shapes-web/backend


##Implementation

Phase 1: frontend

Start off with setting up the frontend (see section Frontend)


##Phase 2: backend

Let's continue with the backend part (see section Backend).

##Phase 3: test communication between frontend and backend

To make sure that both the frontend and the backend works and that they can communicate, create a simple React component that sends the message "Hello world!" to the backend when a button is clicked and display the response from the backend. 

The backend responds by reversing the received message pluds adding current date.

Example: "Hello World!" -> "!dlroW olleH 14.11.2025"

Use RESTful protocol for communicating between the frontend and the backend.

The REST route should be /hello-world

###Specs:

####Frontend

- create a HelloWorld component with a button named "Click me!" and a placeholder for the server response
- use POST for sending
- send the message in a variable named "message"


####Backend

- create a simple route handler that listens to the route /hello-world and processes the request according to specs


##Phase