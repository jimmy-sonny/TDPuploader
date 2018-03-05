# TDPuploader
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)
![Language: Python3](https://img.shields.io/badge/language-python3-blue.svg)

# Intro
A Python program to automatically upload "Tecniche di Programmazione" videolectures on YouTube

```
$ ./tdpuploader.py

TDPuploader - Upload TdP lesssons on your Youtube channel
by Andrea Marcelli (!) v.0.1

23:29:42 INFO:: Donwloading Rgistro TdP
23:29:43 INFO:: Found "Registro" TDP
23:29:43 INFO:: Parsing "Registro" TDP
23:29:43 INFO:: Index:1 1 06/03/2018 16:00-17:30 L Introduzione al corso Fulvio Corno
23:29:43 INFO:: Index:2 2 06/03/2018 17:30-19:00 L Introduzione a JavaFX Fulvio Corno
23:29:43 INFO:: Index:3 3 12/03/2018 10:00-11:30 L Programmazione in JavaFX Fulvio Corno
23:29:43 INFO:: Index:4 4 13/03/2018 16:00-17:30 L Java Objects, Java Collections Fulvio Corno
23:29:43 INFO:: Index:5 5 13/03/2018 17:30-19:00 EA Java Objects, Java Collections Andrea Marcelli
23:29:43 INFO:: Found 5 candidate lectures
Choose a lecture (range: 1-5):
...
```

# Requirements
Requires Python 3.4+

```
git clone --recurse-submodules https://github.com/jimmy-sonny/TDPuploader
cd TDPuploader
pip install -r requirements.txt
```

# Example

```
./tdpuploader.py -v ../lecture_example.mp4 -cs my_client_secret.json
```

# Licensing

**Copyright © 2017 Andrea Marcelli.**

*TDPuploader* is licensed under the 2-Clause BSD License ([BSD-2-Clause](https://opensource.org/licenses/BSD-2-Clause)).
