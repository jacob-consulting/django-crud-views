# Abstract

On every Crud-View one must define the model.
This is redundant since every Crud view has the ViewSet defined, which also has the model.

# Tasks

- Make the model optional on Crud-Views i.e., by using a class property to access the model via the ViewSet  
- Make sure that a manual override of the model in the Crud-View is still possible
- Update the example apps in /examples
- Update the tests
- Update the documentation
