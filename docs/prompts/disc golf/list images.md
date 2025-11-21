#List images

I need a page where I can see all added images where upload_status = 'SUCCESS'.

##Specs:
- detected border should be rendered for each image
- border is "read-only", no need to be able to modify it
- if resizing the page causes image size to change, the border should re-render to reflect new image size
- at this point, no pagination is required
- re-rendering border will most likely be needed in the component that handles adding new images, so try to use same code
- route for this page should be "/". As this route is already used by <ShapeDetectionPage> component, modify routes so that <ShapeDetectionPage> uses route "/discs/shape-detection" . Remember to change path and text in the menu items
- page file for this component should be DiscsPage.tsx

