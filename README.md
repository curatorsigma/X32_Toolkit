# X32 Toolkit

## Usecases

This toolkit was designed for sessions with near-identical routing/patching needs in mind. Going from any number of X32.scn files and LOGIC.logicx files as a base (think 1 for FoH, 1 for the Monitor desk, 1 logic project for multitrack recording), the Toolkit will create Scenes and Projects for every Session, renaming channels everywhere.

X32_Toolkit can also help you move channels around in a regular Scene, preserving input routing for a specific channel name (the channel Drag-and-Drop the X32 really misses :)

## Getting Started

### Building multiple Scenes from scratch

```bash
python session_build.py Example.csv Bases Scenes
```
will create (or override within!!!) a Directory ./Scenes/ and create the Scenes and LOGIC.logicx-files in that directory, according to the names in ```Example.csv```, using the Scenes and Projects in ```Bases``` as Template.

```bash
python x32_toolkit.py scenename.scn
```
will spawn an interactive session, working on ```scenename.scn```. Make sure to ```export``` your changes once you are done.
