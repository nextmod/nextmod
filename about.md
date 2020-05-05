# Nextmod
Nextmod is a Static Site Generator for Mod Indexes.

## Design

### Pages
#### Required
* HTML5
* CSS3
#### Optional
* ES6
#### Constraints
* Simple human readable file formats
* No js required for basic features
### Generator
* python3
* ...

#### Q&A
##### Why do the links point to ugly index.html files instead of nice directories?
This enabled the pages to be used without a WebServer.
##### Why indent with tabs and not spaces?
Tabs allow any author to configure the width according to their needs.
Tabs also serve as a quick overview of the current indentaion level if the editor displays whitespace.


## mod-info.md file structure
~~~.md
# Name
My Special Mod

# Created by
Myself

# Category
Cool Category

# Description
Makes the game more awesome

# Release date
2020-01-01 12:11

# Last update date
2020-01-01 12:11

# Version
1.0

# Changelog
## Version 1.0
* Released my first mod

# Credits
* Someone

# Permissions
You can do anything.
~~~

