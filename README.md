# beurer-scale-data
A dash application to review weight and composition data from Bluetooth-enabled Beurer scales.

![Screenshot from 2021-07-04 18-16-07](https://user-images.githubusercontent.com/22397839/124392080-0f320780-dcf4-11eb-9a6b-1f0015c8536e.png)

-------------------------

**Motivation:** As an owner of a Bluetooth-enabled "smart" Beurer scales, I am very underwhelmed with their interface for reviewing the measurements done with the scales. To give an example, below to the left is a snapshot from the home screen of their Beurer Health Manager app. Frankly, it would be difficult to make this plot *less* informative... While, with multiple clicks, one can get somewhat more useful plots in the app (see the right-hand plot below, note that there is no way to view it in landscape mode, pan, or zoom the data...), the interface is far from intuitive or easy-to-use. Sadly, the web interface is not much better.

<p align="center">
<img src="https://user-images.githubusercontent.com/22397839/123541724-3d3ca800-d746-11eb-9a4d-0e650efb6b1e.jpg" alt="Beurer Health Manager home screen" width="25%"/>     <img src="https://user-images.githubusercontent.com/22397839/123541725-3e6dd500-d746-11eb-92a8-aacdc3759973.jpg" alt="Beurer Health Manager details screen" width="25%"/></td>
</p>

Fortunately, Beurer does allow you to download the .csv files with all the information downloaded from the scales (thanks, EU! :) ). Thus, I decided to create a simple Dash interface to view the data from my scales.

-------------------------
