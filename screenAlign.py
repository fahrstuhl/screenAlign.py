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

    def findBiggestCommonResolutionForMonitors(self, monitors):
        monitorResolutions = self.findResolutionsForMonitors(monitors)
        union = set()
        for resolutions in monitorResolutions.values():
            union |= resolutions
        for resolutions in monitorResolutions.values():
            union &= resolutions
        resolution = max(union, key=self.calculateArea)
        return resolution

    def findResolutionsForMonitors(self, monitors):
        monitorResolutions = dict()
        resolution = set()
        i = 0
        outputs = [x for x in self.outputRegex.finditer(self.xrandrOutput)]
        for i in range(len(outputs)):
            output = outputs[i]
            try:
                nextOutput = outputs[i+1]
                nextOutputStart = nextOutput.start()
            except IndexError:
                nextOutputStart = -1
            outputName = output.group('outputName')
            for monitor in monitors:
                if monitor == outputName:
                    substring = self.xrandrOutput[output.end():nextOutputStart]
                    monitorResolutions[outputName] = set(self.resolutionRegex.findall(substring))
        return monitorResolutions


    def calculateArea(self, resolutionString):
        split = resolutionString.split('x')
        return int(split[0]) * int(split[1])

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
        arguments = [self.makeArgumentList(self.defaultMonitor), self.makeArgumentList(additionalMonitor, additionalPos)]
        self.setCommand(arguments)

    def setCommand(self, arguments):
        self.command = [self.xrandr]
        for argument in arguments:
            self.command.extend(argument)

    def makeArgumentList(self, outputName, position=None, resolution=None, off=False):
        outputArgument = ['--output', outputName]
        if off:
            arguments = outputArgument + ['--off']
        else:
            if resolution is not None:
                resolutionArgument = ['--mode', resolution]
            else:
                resolutionArgument = ['--auto']
            if position is not None:
                positionArgument = ['--pos', position]
            else:
                positionArgument = []
            if off:
                offArgument = ['--off']
            else:
                offArgument = []
            arguments = outputArgument + positionArgument + resolutionArgument
        return arguments

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

    def clone(self):
        monitors = self.findConnectedMonitors()
        resolution = self.findBiggestCommonResolutionForMonitors(monitors)
        arguments = []
        for monitor in monitors:
            arguments.append(self.makeArgumentList(monitor, resolution=resolution))
        self.setCommand(arguments)
        self.setLayout()

    def external(self):
        additionalMonitor = self.findFirstAdditionalMonitor()
        arguments = [
                self.makeArgumentList(self.defaultMonitor, off=True),
                self.makeArgumentList(additionalMonitor)
                ]
        self.setCommand(arguments)
        self.setLayout()

if __name__ == "__main__":
    l = Layout('LVDS1')
    l.setBelowMiddle()
