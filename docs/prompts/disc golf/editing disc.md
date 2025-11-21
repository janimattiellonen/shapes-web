#Editing discs


It should be possible to edit a disc's details. A user may accidentally set the border incorrectly and save. Instead of just deleting the disc, I should be able to modify the border and save changes.

As the save operation may crop the image a bit, it should be possible to "reset" the state and show the original image. 

As the user saves the changes, the system may need to replace the cropped version.

The UI already has a button "Reset border" so the new button could be "Reset image". What the "Reset image" does, is that the original image is loaded instead of the cropped image. No additional changes needs to be persisted at this moment. Only if the user clicks either on the "Save border" or the "Save disc" buttons, should any modifications be persisted.

If unsure, ask for clarifications.
