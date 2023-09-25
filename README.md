# drom-parser-chatbot-ru_doesnt_work
---
My very first project is a chat bot parser of cars from the drom website. Combined everything into one file with sqlite3 and attempts to use multithreading. 

---
At the moment it does NOT WORK, because the site has changed the necessary attributes and tags, respectively, you will need to change them. There are a lot of crutches and flaws here, because this is my first big project.

---
***This program does not violate the rules of the site [drom](drom.ru), because it is not used for commercial purposes and does not take money***

---

Its past working functionality:

  * A kind of graphical interface is registered through the vk keyboard for user interaction

  * Displaying information to the user in the form of a "carousel"
  
  * Saving information to the sqlite database
  
  * Tracking new cars by user parameters
  
  * Car offers by geographical location (Send your location)
  
  * Ability to customize specific car offers
  
  * Crooked multithreading, because sqlite often swears at access

> For those who still decide to sort out this mess :), first of all you will have to change attributes and tags, then divide everything and connect object-oriented programming)
