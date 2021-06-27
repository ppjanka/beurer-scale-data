# beurer-scale-data
A dash application to review weight and composition data from Bluetooth-enabled Beurer scales.

-------------------------

As an owner of a Bluetooth-enabled "smart" Beurer scales, I am very underwhelmed with their interface for reviewing the measurements done with the scales. To give an example, here is a snapshot from the home screen of their Health Manager app.

![SmartSelect_20210616-130058_HealthManager](https://user-images.githubusercontent.com/22397839/123541266-e6ce6a00-d743-11eb-8078-c84b763bbbae.jpg){width=25%}

Frankly, it would be difficult to make this plot *less* informative... While, with multiple clicks, once can get somewhat more useful plots in the app, the interface is far from intuitive or easy-to-use. Sadly, the web interface is not much better.

Fortunately, Beurer does allow you to download the .csv files with all the information downloaded from the scales (thanks, EU! :) ). Thus, I decided to create a simple Dash interface to view the data from my scales.

-------------------------
