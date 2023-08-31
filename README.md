# python-email-job-scraper
Using Python and GoogleAPIs, will look through the chosen email's HTML and add jobs to spreadsheet
Things to note: 
- Because this is a project designed for my computer, I would love to have the community add/edit so it is universally compatible with different email suppliers and job websites!
- A lot of the parsing is very sloppy and would love a simpler method to find the valuable data. If you have any please suggest changes!
- Currently supports LinkedIn, Monster, Handshake, and Indeed (Glassdoor altered their HTML, so it is not updated)
- Future goals for this project to account for quick changes:
  * Each potential email type (probably by Title or Company) is separated into different files
  * Compatibility with most common email clients (Outlook, Gmail, Apple...)
  * Incorporate price data for each job type
  * Simplify Spreadsheet to be easy to read for new users (put in order)
 
If directly using this product: 
- Check all blacklists to determine if you would like those to be blacklisted. Some things are formatting-related, others are preferences for states/cities/countries that I would not want to work in.
- Check the spreadsheet settings to determine if the data is in your correct order and in the correct location
