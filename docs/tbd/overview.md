# Overview


## Layout Overview

- Screenshot with explanation of the layout.
- Definitions:
  - Text objects: title, paragraph, ...
  - Context actions
  - List actions

## CRUD Views

### Keys
- What are keys?
- Views are defined by keys (string literal)
- Use them in the configuration to link views together. 
- You do not need to write {% url 'app:author-detail author.id ' %} in your templates.

### Predefined Views and their keys
- CreateView: create 
- ListView: list
- DetailView: detail
- UpdateView: update
- DeleteView: delete
- UpView: up
- DownView: down

### Configuration
- minimal configuration
- text label templates and code

### Permissions
- why? motivation

### DetailView
- Properties and PropertyGroup
- Labels
- View methods vs model fields
- Renderers, list of renderers
- template tags