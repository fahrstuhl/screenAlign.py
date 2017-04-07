#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
import re
from subprocess import run, PIPE

class Layout(object):

    def __init__(self, defaultMonitor):
        self.xrandr = 'xrandr'
        self.xrandrOutput = self.getxrandrOutput()
        self.resolutionRegex = re.compile("(?P<resolution>[0-9]{3,4}x[0-9]{3,4})\s+?.*?")
        self.preferredResolutionRegex = re.compile("(?P<preferredResolution>[0-9]{3,4}x[0-9]{3,4})\s+?.*?\+")
        self.outputRegex = re.compile("(?P<outputName>\S*)\s+connected")
        self.defaultMonitor = defaultMonitor
        self.defaultResolution = self.findPreferredResolutionForMonitor(self.defaultMonitor)
        self.defaultPos = {'x': 0, 'y': 0}

    def getxrandrOutput(self):
        output = run([self.xrandr], stdout=PIPE).stdout.decode()
        return output

    def makeResolutionDict(self, resolutionString):
        split = resolutionString.split('x')
        return {'x': split[0], 'y': split[1]}

    def findConnectedMonitors(self):
        return self.outputRegex.findall(self.xrandrOutput)

    def findPreferredResolutionForMonitor(self, monitorName):
        for output in self.outputRegex.finditer(self.xrandrOutput):
            outputName = output.group('outputName')
            if outputName == monitorName:
                substring = self.xrandrOutput[output.end():]
                searchForPreferred = self.preferredResolutionRegex.search(substring)
                if searchForPreferred is not None:
                    preferredResolution = searchForPreferred.group('preferredResolution')
                else:
                    preferredResolution = self.resolutionRegex.search(substring).group('resolution')
                return self.makeResolutionDict(preferredResolution)

    def findFirstAdditionalMonitor(self):
        monitors = self.findConnectedMonitors()
        monitors.remove(self.defaultMonitor)
        monitorName = monitors[0]
        return monitorName

    def bottomAlign(self, resolution):
        verticalAlignment = int(self.defaultResolution['y']) - int(resolution['y'])
        return verticalAlignment

    def topAlign(self, resolution):
        return 0

    def aboveOf(self, resolution):
        verticalAlignment = -int(resolution['y'])
        return verticalAlignment

    def belowOf(self, resolution):
        verticalAlignment = int(self.defaultResolution['y'])
        return verticalAlignment

    def rightOf(self, resolution):
        horizontalAlignment = int(self.defaultResolution['x'])
        return horizontalAlignment

    def leftOf(self, resolution):
        horizontalAlignment = -int(resolution['x'])
        return horizontalAlignment

    def middleAlign(self, resolution):
        horizontalAlignment = int(self.defaultResolution['x']) - int(resolution['x']) 
        horizontalAlignment //= 2
        return horizontalAlignment

    def coordinatesToString(self, coordinates):
        return str(coordinates['x']) + 'x' + str(coordinates['y'])

    def setAlignment(self, horizontalAlignment, verticalAlignment):
        additionalMonitor = self.findFirstAdditionalMonitor()
        additionalResolution = self.findPreferredResolutionForMonitor(additionalMonitor)
        additionalPos = {'x': horizontalAlignment(additionalResolution), 'y': verticalAlignment(additionalResolution)}
        additionalPos = self.coordinatesToString(additionalPos)
        self.setCommand(additionalMonitor, additionalPos)

    def setCommand(self, outputName, position):
        self.command = [self.xrandr,
                '--output', self.defaultMonitor,
                '--pos', '0x0',
                '--auto',
                '--output', outputName,
                '--auto',
                '--pos', position,
                ]

    def setLayout(self):
        print(self.command)
        run(self.command)

    def setRightOfBottom(self):
        self.setAlignment(self.rightOf, self.bottomAlign)
        self.setLayout()

    def setLeftOfBottom(self):
        self.setAlignment(self.leftOf, self.bottomAlign)
        self.setLayout()

    def setLeftOfTop(self):
        self.setAlignment(self.leftOf, self.topAlign)
        self.setLayout()

    def setAboveMiddle(self):
        self.setAlignment(self.middleAlign, self.aboveOf)
        self.setLayout()

    def setBelowMiddle(self):
        self.setAlignment(self.middleAlign, self.belowOf)
        self.setLayout()

if __name__ == "__main__":
    l = Layout('LVDS1')
    l.setBelowMiddle()
