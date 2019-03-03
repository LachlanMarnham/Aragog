# Aragog
Aragog is a web crawler built to scrape all of the urls from www.thomann.de. While there are some aspects which are 
specific to that domain, the main feature which stops it being a general web crawling solution for arbitrary domain
is the parser I built to handle the robots.txt. This is somewhat optimised for thomann.de. For example, we assume that 
'we' (i.e. whoever is deploying the Aragog parser) are not famous enough to have specific user-agent rules. The crawler 
was written in such a way that all of the robots.txt parsing logic is built into a mixin which could be switched out
in a straight forward way so that this can be fixed later.

### Assumptions
I'm working under the following assumptions here:
- We can't DOS the target site!!! For this reason I'm throttling the request rate to 2 per second
- We aren't a famous user-agent (see above)
- That the requirement "...write a web crawler that will extract all the URLs from a website..."
means: catalogue every url linked to from the www.thomann.de domain, but only *follow* urls which point to another page 
at the same domain. This means we will stop crawling after we have all local domains, but that we will still
keep track of all non-local urls referenced from www.thomann.de. I think this is in the spirit of the goal, which 
is to "write a web crawler that will extract all the URLs from a website so that they could later be scraped for 
product data".
- For a first pass, concurrency == over-engineering. This might be controversial. However, in the prototyping phase I 
found that the time taken to perform a request, parse the DOM, and extract all urls was around 400ms on average. 
There is a large variance (e.g. the homepage has a lot of links, and took around 900ms). Given that we spend <500ms 
waiting on I/O (on average) and that our goal is throttle the request rate at 2 per second anyway, concurrency is probably
not a top priority for a fist pass at this problem


### TODO
- Write an arbitrary robots.txt parser (I think I'm probably not *that* far off to be honest, but my unit tests were written
with the target domain in the back of my mind, so I'm potentially missing some things necessary for generality)
- Build in concurrency (might have been a bit much for a first pass at the project, but 50ms here and there would really
add up if I were crawling www.amazon.com instead of www.thomann.de!!!!). I'd potentially want this to be achieved with
multiprocessing, so I could split the requests, parsing, queuing and storage into different microservices. This would
be better for scalability if one of these constituents is less performant than the others, for example.

### Set up:
Clone the repo
```console
[you@localhost: ~]$ git clone git clone https://github.com/LachlanMarnham/Aragog.git
...
[you@localhost: ~]$ cd Aragog
```
Create a virtual environment, e.g....
```console
[you@localhost: Aragog]$ virtualenv --python=python3.6 venv
```
...and activate it
```console
[you@localhost: Aragog]$ source venv/bin/activate
```
Install the packages
```console
[you@localhost: Aragog]$ pip install -r requirements.txt
```

### Run the code
TODO

### Run the tests
TODO

![follow the spiders](https://media.giphy.com/media/axWsKEl0Nrppm/giphy.gif)