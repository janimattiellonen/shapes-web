#Adding multiple images


Adding images one by one using the web frontend is inefficient, if I have hundreds or thousands of images.

I need a command line approach. I'd like to be able to just provide a path to a directory containing images I want to be added.

Basically the same thing as the /register route in routes.py file without the http protocol related operations.


Specs:

- as there may be several hundreds of images, some kind of progress report shoudl be printed. For example: "200/999 images processed", where the process is updated every 100th image.
- when all images have been processed display the amount of sucessfull and failed items
- don't stop on one error, log the error and continue
- store the paths of saved images and paths of images that were not saved including an error message, if available, into a text file. Add current time to the file name. Format of filename: 'process-report-[YYYY-MM-DD hh:mm:ss].txt. Store this file in the same directory as where the source files are in


Implementation details:

- the cli tool will basically do the same thing as the /register route in routes.py file without the http protocol related operations. Extract image saving related code from /register route into an own file and and utilize the newly created functions in the cli tool and in the /register route.