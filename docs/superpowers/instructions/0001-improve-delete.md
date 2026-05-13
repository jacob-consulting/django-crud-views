# Improve Delete

I want to improve the DeleteView.

Currently, we have a `CrispyDeleteForm` that is used in the DeleteView. 
This form is a simple form that only has a submit button and a checkbox to confirm the deletion.

## Cascading Deletes

### Motivation 
In Django Admin there is a feature that shows you all the related objects that will be deleted when you delete an object. 
This is a very useful feature that helps you to understand the consequences of deleting an object.

### Idea
I want to implement a similar feature in our DeleteView. 
When the user clicks on the delete button, they should see a list of all the related objects that will be deleted.
This should be configurable on the DeleteView if this information should be shown or not.

### Template
For the rendering of the related objects, which can be nested, 
we need a template, which is included in the DeleteView template.

That way projects can customize the rendering of the related objects by overriding the template.

### Linking to related objects
The question is to whether linking to the related objects in the list is a good idea or not?
If so, can this be customized as well?

### Permissions
How does this work with the permission system?
I think of model based permissions, but also django-guardian per object permissions.

## Delete Protection

I want a custom behavior that checks if an object can be deleted or not.

This could be just done in a customized DeleteForm in the clean method.
The errors would be displayed as non field errors in the form.

Is this good or do you have a better idea?
