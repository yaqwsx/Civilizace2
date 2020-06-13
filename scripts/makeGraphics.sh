#!/usr/bin/env bash

BUILD_DIR="_graphics"

TEAMS="cerni cerveni oranzovi zluti zeleni modri fialovi ruzovi univerzal"

declare -A COLORS

COLORS["cerni"]="8795A1"
COLORS["cerveni"]="CC1F1A"
COLORS["oranzovi"]="F6993F"
COLORS["zluti"]="FFED4A"
COLORS["zeleni"]="1F9D55"
COLORS["modri"]="2779BD"
COLORS["fialovi"]="794ACF"
COLORS["ruzovi"]="EB5286"
COLORS["univerzal"]="FFFFFF"

declare -A ID

ID["cerni"]="1"
ID["cerveni"]="2"
ID["oranzovi"]="3"
ID["zluti"]="4"
ID["zeleni"]="5"
ID["modri"]="6"
ID["fialovi"]="7"
ID["ruzovi"]="8"
ID["univerzal"]="-1"

function lower {
    echo $1 | tr '[:upper:]' '[:lower:]'
}

function colorArg {
    echo $1 | python -c 'h=input(); print("-r {} -g {} -b {}".format(*tuple(int(h[i:i+2], 16) for i in (0, 2, 4))))'
}

function generateTeam() {
    DIR=${BUILD_DIR}/$1
    mkdir -p $DIR
    # Generate name tags
    python manage.py plotTeamCard --output $DIR/nameTag.pdf --id "${ID[${1}]}" $(colorArg "${COLORS[${1}]}")
    # Generate techTree
    python manage.py plotTech --buildDir $DIR/tech $(colorArg "${COLORS[${1}]}")
    # Generate buildings
    cat graphics/budovy-template.svg | \
         sed -e "s/fill:#ff0000/fill:#$(lower ${COLORS[${1}]})/g"      | \
         sed -e "s/stroke:#ff0000/stroke:#$(lower ${COLORS[${1}]})/g"  | \
         sed -e "s/fill:#0000ff/fill:none/g"      | \
         sed -e "s/stroke:#0000ff/stroke:none/g"  > $DIR/budovy.svg
    inkscape $DIR/budovy.svg --export-pdf=$DIR/budovy.pdf
    # Generate dices
    cat graphics/dices-template.svg | \
         sed -e "s/fill:#0000ff/fill:#$(lower ${COLORS[${1}]})/g"      | \
         sed -e "s/stroke:#0000ff/stroke:#$(lower ${COLORS[${1}]})/g" > $DIR/dices.svg
    inkscape $DIR/dices.svg --export-pdf=$DIR/dices.pdf
}

function generateCommon() {
    DIR=${BUILD_DIR}/common
    mkdir -p $DIR
    # Generate vyrobas
    python manage.py plotVyroba --buildDir $DIR/vyroba
    # Generate wonders
    cat graphics/divy.svg | \
         sed -e "s/fill:#ff0000/fill:none/g"      | \
         sed -e "s/stroke:#ff0000/stroke:none/g" > $DIR/divy.svg
    inkscape $DIR/divy.svg --export-pdf=$DIR/divy.pdf
    # Generate tiles
    cat graphics/dlazdice-cesta1.svg | \
         sed -e "s/fill:#ff0000/fill:none/g"      | \
         sed -e "s/stroke:#ff0000/stroke:none/g" > $DIR/dlazdice-cesta1.svg.svg
    inkscape $DIR/dlazdice-cesta1.svg --export-pdf=$DIR/dlazdice-cesta1.svg
    cat graphics/dlazdice-cesta2.svg | \
         sed -e "s/fill:#ff0000/fill:none/g"      | \
         sed -e "s/stroke:#ff0000/stroke:none/g" > $DIR/dlazdice-cesta2.svg
    inkscape $DIR/dlazdice-cesta2.svg --export-pdf=$DIR/dlazdice-cesta2.pdf
    cat graphics/dlazdice.svg | \
         sed -e "s/fill:#ff0000/fill:none/g"      | \
         sed -e "s/stroke:#ff0000/stroke:none/g" > $DIR/dlazdice.svg
    inkscape $DIR/dlazdice.svg --export-pdf=$DIR/dlazdice.pdf
    # Generate dots
    inkscape graphics/dots.svg --export-pdf=$DIR/dots.pdf
}

# for team in $TEAMS; do
#     echo Generating $team
#     generateTeam $team &
# done

# echo Generating common
# generateCommon

# wait

echo Combining results together...
DIR=$BUILD_DIR/final

# Vyroby
pdftk $BUILD_DIR/common/vyroba/vyr-*.pdf cat output "$DIR/vyroby-9x.pdf"

# Enhancements
pdftk $BUILD_DIR/common/vyroba/enh-*.pdf cat output "$DIR/vylepseni-9x.pdf"

# Wonders
cp $BUILD_DIR/common/divy.pdf "$DIR/divy-2x.pdf"

# Roads
pdftk $BUILD_DIR/common/dlazdice*.pdf cat output "$DIR/dlazdice-2x.pdf"

# Dots
cp $BUILD_DIR/common/dots.pdf "$DIR/tecky-2x.pdf"

# NameTags
TAG_FILES=""
for team in $TEAMS; do
    TAG_FILES="$TAG_FILES $BUILD_DIR/$team/nameTag.pdf"
done
pdftk $TAG_FILES cat output "$DIR/jmenovky-12x.pdf"

# Techy
TECH_FILES=""
for team in $TEAMS; do
    TECH_FILES="$TECH_FILES $(find $BUILD_DIR/$team -name 'tech-*.pdf')"
    TECH_FILES="$TECH_FILES $(find $BUILD_DIR/$team -name 'build-*.pdf')"
done
pdftk $TECH_FILES cat output "$DIR/technologie-1x.pdf"

#  Budovy
BUILD_FILES=""
for team in $TEAMS; do
    BUILD_FILES="$BUILD_FILES $BUILD_DIR/$team/budovy.pdf"
done
pdftk $BUILD_FILES cat output "$DIR/budovy-1x.pdf"

#  Budovy
DICE_FILES=""
for team in $TEAMS; do
    DICE_FILES="$DICE_FILES $BUILD_DIR/$team/dices.pdf"
done
pdftk $DICE_FILES cat output "$DIR/kostky-1x.pdf"