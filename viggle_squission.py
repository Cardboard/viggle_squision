from svgpathtools import svg2paths2, wsvg, CubicBezier, Path, Line
#from svglib.svglib import svg2rlg
#from reportlab.graphics import renderPM
from wand.api import library
from wand.image import Image
from wand.color import Color
from lxml import etree, objectify

from random import randint
import copy
import os, sys


svg_file = ''
num_frames = 0
viggle_amount = 5
usage = 'usage: viggle_squission.py svg_filename_sans_extension num_of_frames (amount_of_viggle)'

# use command line arguments to choose the svg file to use and number of frames
if (len(sys.argv) == 3 or len(sys.argv) == 4) and isinstance(sys.argv[1], str):
    svg_file = sys.argv[1] # filename without extension
else:
    print(usage)
    sys.exit(2)
try:
    num_frames = int(sys.argv[2])
    if not(num_frames > 0):
        print(usage)
        sys.exit(2)
except ValueError:
    print(usage)
    sys.exit(2)

if len(sys.argv) == 4 and int(sys.argv[3]) >= 1:
    viggle_amount = int(sys.argv[3])

def wiggle(pt):
    return complex(pt.real + randint(-viggle_amount, viggle_amount), pt.imag + randint(-viggle_amount, viggle_amount))

#!TODO
# * transparent PNGs
# * command line usage (svg filename, number of frames)
# * output PNGs to an appropriately named folder

# check for 'serif' in the xml and delete it because it seems to ruin things
parser = etree.XMLParser(remove_blank_text=True)
src = etree.parse(svg_file + '.svg', parser)
objectify.deannotate(src, xsi_nil=True)
etree.cleanup_namespaces(src)
etree.ElementTree(src.getroot()).write(svg_file + '.svg', pretty_print=True)

print('working . . .')

# make a directory to hold all the output PNG frames
if not(os.path.isdir(svg_file)):
    os.mkdir(svg_file)

for FRAME in range(num_frames):
    paths, attr, svg_attr= svg2paths2(svg_file + '.svg')
    newpaths = []
    j = 0
    for path in paths:
        #print('\nparsing path of length {}'.format(len(path._segments)))
        path = paths[j]
        path_attr = attr[j]
        pathlist = []
        newpath = Path()
        x = copy.copy(path[0][0])
        cornerstone = wiggle(x)

        for k in range(len(path)):
            segment = path[k]
            prev_segment = pathlist[k-1] if not k==0 else None

            #print('\n{}\n{}'.format(segment, prev_segment))

#            if type(segment) == CubicBezier:
#                prev_e = copy.copy(path[0][3]) # first end point is the end of the first path
#            elif type(segment) == Line:
#                prev_e = copy.copy(path[0][1])

                #s = copy.copy(prev_e)

            # current segment is a CubicBezier
            if type(segment) == CubicBezier:
                # first segment is a CubicBezier
                if prev_segment == None:
                    #s = copy.copy(segment[0])
                    c1 = copy.copy(segment[1])
                    c2 = copy.copy(segment[2])
                    e = copy.copy(segment[3])
                    e = wiggle(e)
                    pathlist.append(['CubicBezier', cornerstone, c1, c2, e])
                elif prev_segment[0] == 'CubicBezier':
                    s = copy.copy(prev_segment[4])
                    c1 = copy.copy(segment[1])
                    c2 = copy.copy(segment[2])
                    e = copy.copy(segment[3])
                    e = wiggle(e)
                    pathlist.append(['CubicBezier', s, c1, c2, e])
                elif prev_segment[0] == 'Line':
                    s = copy.copy(prev_segment[2])
                    c1 = copy.copy(segment[1])
                    c2 = copy.copy(segment[2])
                    e = copy.copy(segment[3])
                    e = wiggle(e)
                    pathlist.append(['CubicBezier', s, c1, c2, e])

            # current segment is a Line
            if type(segment) == Line:
                # first segment is a Line
                if prev_segment == None:
                    #s = copy.copy(segment[0])
                    e = copy.copy(segment[1])
                    e = wiggle(e)
                    pathlist.append(['Line', cornerstone, e])
                elif prev_segment[0] == 'CubicBezier':
                    s = copy.copy(prev_segment[4])
                    e = copy.copy(segment[1])
                    e = wiggle(e)
                    pathlist.append(['Line', s, e])
                elif prev_segment[0] == 'Line':
                    s = copy.copy(prev_segment[2])
                    e = copy.copy(segment[1])
                    e = wiggle(e)
                    pathlist.append(['Line', s, e])

        # edit the last path's start and end (its end must be the first segment's start (AKA 'cornerstone'))
        initial = pathlist[0]
        final_segment = pathlist[-1]

        # there's no "penultimate" segment if the path is only two points
        if len(pathlist) > 2:
            penult_segment = pathlist[-2]
            if type(final_segment) == CubicBezier:
                if type(penult_segment) == CubicBezier:
                    s = copy.copy(penult_segment[4])
                    c1 = copy.copy(final_segment[1])
                    c2 = copy.copy(final_segment[2])
                    e = copy.copy(initial[1])
                    pathlist[-1] = (['CubicBezier', s, c1, c2, e])
                elif type(penult_segment) == Line:
                    s = copy.copy(penult_segment[2])
                    c1 = copy.copy(final_segment[1])
                    c2 = copy.copy(final_segment[2])
                    e = copy.copy(initial[1])
                    pathlist[-1] = (['CubicBezier', s, c1, c2, e])
            elif type(final_segment) == Line:
                if type(penult_segment) == CubicBezier:
                    s = copy.copy(penult_segment[4])
                    e = copy.copy(initial[1])
                    pathlist[-1] = (['Line', s, e])
                elif type(penult_segment) == Line:
                    s = copy.copy(penult_segment[2])
                    e = copy.copy(initial[1])
                    pathlist[-1] = (['Line', s, e])

        #for i in range(len(pathlist)):
        #    print('-> {}\t{}'.format(pathlist[i][3], pathlist[(i + 1) % (len(pathlist)) ][0]))
        #    print('<-: {}\t{}'.format(pathlist[i][0], pathlist[(i -1) % (len(pathlist)) ][3]))

        for i in pathlist:
            if i[0] == 'CubicBezier':
                newpath.append(CubicBezier(i[1], i[2], i[3], i[4]))
            elif i[0] == 'Line':
                newpath.append(Line(i[1], i[2]))

        newpaths.append(newpath)
        j+=1

    print('\tfinished generating frame {}'.format(FRAME+1))

    # export svg
    #newpaths.reverse()
    svg_newfile = svg_file + '_' + str(FRAME+1) + '.svg'
    wsvg(newpaths, attributes=attr, svg_attributes=svg_attr, filename=svg_newfile)


    # fix the xml
    src = etree.parse(svg_file + '.svg', parser)
    dest = etree.parse(svg_newfile, parser)


    gees = src.findall('.//{http://www.w3.org/2000/svg}g')
    dest_paths = dest.findall('.//{http://www.w3.org/2000/svg}path')

    for g in gees:
        paths = src.findall('.//{http://www.w3.org/2000/svg}path')
        # delete paths from source xml before we copy them over to the dest file
        for path in g.getchildren():
            g.remove(path)
        # add the g to the dest's xml
        dest.getroot().append(g)

    # now we just need to parent the paths to the gs
    dest_gees = dest.findall('.//{http://www.w3.org/2000/svg}g')
    for i in range(len(dest_gees)):
        dest_gees[i].append(dest_paths[i])


    etree.ElementTree(dest.getroot()).write(svg_newfile, pretty_print=True, encoding='utf-8', xml_declaration=True)

    # convert each svg to a png
    png_filename = os.path.join(svg_file, svg_file + '_' + str(FRAME+1) + '.png')
    svg_filename = svg_file + '_' + str(FRAME+1) + '.svg'


    print('\t\tsaving {}'.format(png_filename))

    with Image(filename=svg_filename) as image:
        with Color('transparent') as background_color:
            library.MagickSetBackgroundColor(image.wand, background_color.resource)
        png_image = image.make_blob('png32')
    with open(png_filename, 'wb') as out:
        out.write(png_image)

    '''
    drawing = svg2rlg(svg_newfile)
    renderPM.drawToFile(drawing, os.path.join(svg_file, png_filename), fmt='PNG', mask='auto')
    '''

    # delete each svg file (optional, of course)
    os.remove(svg_newfile) # good riddance
    print('\t\tdeleted {}'.format(svg_newfile))
