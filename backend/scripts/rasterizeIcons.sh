#!/usr/bin/env bash

convert() {
    inkscape $2 --actions="select-all;fit-canvas-to-selection;export-type:png;export-width:$1;export-do" -o $3

}

for f in data/icons/*.svg; do
    echo Processing $f

    lgname="${f%.svg}-lg.png"
    convert 350px $f $lgname

    mdname="${f%.svg}-md.png"
    convert 180px $f $mdname

done
