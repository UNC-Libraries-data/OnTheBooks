# Software Installation Documentation 
### 1. Install the Windows Subsystem for Linux (Ubuntu):  
* To install Linux, first enable the Windows Subsystem for Linux optional feature by running the following command in Windows Powershell (Start --> Windows Powershell  --> Right click --> Run as Administrator):   
    * _Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux_   
* Restart when prompted 
* From the [Microsoft store](https://www.microsoft.com/en-us/p/ubuntu/9nblggh4msv6?activetab=pivot:overviewtab) Get Ubuntu 
* Click on the install button  
* Click on the launch button 
* Once Installation is complete, create a UNIX user and password 
     
### 2. Install Anaconda Python: 
* Install Anaconda from [Anaconda website](https://www.anaconda.com/distribution/) 
* Download latest Python version (64 Bit - Graphical Installer)  
* Run the Anaconda setup file with default settings 
  
### 3. Install Tesseract: 
* __Windows__: 
    * Install from [Github link](https://github.com/UB-Mannheim/tesseract/wiki) 
    * Click on tesseract-ocr-w64-setup-v4.1.0.20190314 (rc1) 
    * Run the Setup file with default settings 
* __MacOS__: 
    * To install using MacPorts run the command: _sudo port install tesseract_ 
    * To install using Homebrew run the command: _brew install tesseract_  
      
### 4. Install openjpeg
* Open a conda terminal, and execute the following:

      conda install openjpeg
      pip install Pillow --force-reinstall

* Pillow needs to be reinstalled after openjpeg is installed to correctly link to the jpeg2000 decoder.
