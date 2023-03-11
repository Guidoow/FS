# FILE SENDING
## _Send files locally easily and quickly._


FS is a lite module that allows you to send files to a computer connected in the same network just with a single command.

## Features

-   You can send single files or an entire folder.

-   You can choose a specified directory to save the files.

-   Sending method is via the TCP protocol.

&nbsp;


You can see a small sample here, where I use this module to receive some random files and directories.

<a href="https://youtu.be/gh7HNkt1PRg" target="_blank"><img src="https://img.youtube.com/vi/gh7HNkt1PRg/maxresdefault.jpg" alt="Youtube sample"/></a>


&nbsp;


### It is prudent to clarify that this is the first version of this module, and it may contain a few bugs.


&nbsp;

---

## Installation

At your command prompt:

If you want to add it to your packages (pip) or if you want to work, or just save it:

>   pip install git+https://github.com/Guidoow/FS.git

OR

>   python -m pip install git+https://github.com/Guidoow/FS.git


If you just want to experiment with this module, you can implement a more dirty way :$
At your local working space:

>   git clone https://github.com/Guidoow/FS.git



---


## Usage



### Client side

>   python (-m fs | fs.py) client ip:port 
> 
> Example  python -m fs client 192.168.1.10:22000
> 
> Then follow instructions to specify a path to what you want to send.

### Server side

>   python (-m fs | fs.py) server port 
> 
> optional: set a directory to save received files -d | --dir     "PATH_TO_FOLDER" | "." to set default
> 
> Example  python -m fs server 22000 --dir C:\Users\Robert\Images\2023
> 
> Then you are open to listen to a client.

&nbsp;



