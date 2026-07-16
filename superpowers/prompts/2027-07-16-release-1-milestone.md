# Release 1.0.0 Milestone

This product is almost reaching production state.

Let's brainstorm what is needed for this milestone.

# what is on my mind?

## crud_views_plain

This template set, which is a plain HTML template set,
is not used by anyone, event not myself.

Documentation talks about it.

I think we should remove it.

Why?
- it's not used
- it's not documented
- it's not tested
- it's not maintained
- it messes up the /examples/ folder

## examples layout 

As noted in the crud_views_plain section,
I plan to remove the app crud_views_plain.

Therefore, the examples folder `examples/plain/` needs to be removed.

I once came up with this shared module, which will be used only by the bootstrap5 example.

Integrate this into bootstrap5.

## bootstrap5 example

The examples have grown organically while implementing the django-crud-views package.

Therefore, they're a sort of mess.

To get this didactically clean, I think we need to completely re-write the examples.

The goals are:
- make the examples more readable and self-explanatory
- one example per feature
- the home page of one example will be mostly a list view, this should also contain code snippets
- make sure all features are covered and unit tested
- take your time to create real-life app examples that make sense out of the box
- fieldsets examples are the most complex, maybe too complex
- guardian examples are guardian, but not real life applicable
- the examples should align with the documentation tutorial
  - step by step adding stuff to the app
  - also docs FAQ could contribute to the examples

Your task: refine this step, be honest, don't guess.

## documentation

Refine the documentation.

- add a catchy teaser. take your time, this is the hard one
- a tutorial that makes fun, see the example app bootsrap5
- make sure the order of appearance is logical
- make sure reference covers all features

Your task: refine this step, be honest, don't guess.

## README.md

For the GitHub home page, the README.md should be updated.
It is the #1 place of marketing.
The audience is experienced Django developers, who are fed up writing the same stuff over and over again.
It must catch them.
How to run the examples? Must be short, precise and working.

Your task: refine this step, be honest, don't guess, especially the init of the example (linux/Mac/windows) 


# what is on your mind?

What do you think I am missing for release 1.0.0? Be honest, don't guess.

# Tasks

The result of this should be a milestone document, not a concrete plan or spec.
The document should create sub milestones in the right order.

It should already contain enough information for a fresh session to brainstorm a sub milestone, one after the other.

