One Trillion Row Challenge
==========================


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
&nbsp;
[![Version](https://img.shields.io/github/v/release/glentner/1trc?sort=semver)](https://github.com/glentner/1trc)
&nbsp;
[![Python Version](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads)


This project is a playground for the "One Trillion Row Challenge", an extension of the popular
["One Billion Row Challenge"](https://www.morling.dev/blog/one-billion-row-challenge/) (1BRC) from early 2024.
It is shared here for general interest.

Install
-------

The well-known [uv](https://docs.astral.sh/uv/) utility is the best way to install this program.

```shell
uv tool install git+https://github.com/glentner/1trc
```

Build
-----

I've taken some liberties in extending the "format" of the challenge.
You could build the standard 1B row single `measurements.txt` file like so,

```shell
1trc build -N1000 -n1000000 -s -p > measurements.txt
```

However, there is the option (as the `-N` and `-n` options suggest) instead to create
a partitioned dataset of many files of varying sizes in either _CSV_ or _PARQUET_ format.

Building the 1BRC in 1000 separate files in a `data` directory.
Use `-v` instead of `-p` to show logs instead of a progress bar.

```shell
mkdir -p data
1trc build -N1000 -n1000000 -o data
```

Now for the 1TRC, 10k files of 100M rows each in _PARQUET_.
```shell
mkdir -p data
1trc build -N10000 -n100000000 -o data -f parquet
```

Solutions
---------

I think I'll add various implementations of a solution under the `run` subcommand eventually.
This was not the priority initially though.
Feel free