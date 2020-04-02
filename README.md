# Robotest Triage

This repo contains automation to speed up bulk triage of
[Robotest](https://github.com/gravitational/robotest/) failures.

It stems from Walt's personal need to triage nightly failures, where
each nightly run may have 10s (think 40+) individual runs.

## Getting Started
Run `make configure`. Add your personal Jenkins username and token to credentials.json.

You can find your username and create tokens at:

https://jenkins.gravitational.io/user/{username}/configure

Validate that you've input correct credentials by running `make auth`.

Once you're able to authenticate, fetch some data with `make fetch`.

That is everything this does currently!

## Configuration
Tweak job settings in config.json.  It is pretty self explanatory.
