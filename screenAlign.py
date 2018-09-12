#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
import re
from subprocess import run, PIPE

class Layout(object):

    def __init__(self, defaultMonitor):
        self.xrandr = 'xrandr'
        self.xrandrOutput = self.getxrandrOutput()
        self.resolutionRegex = re.compile("(?P<resolution>\d{3,4}x\d{3,4})\s+(?P<framerate>\d{2,3}\.\d{2})\s?(?P<active>\*?)(?P<preferred>\+?)")
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

    def findConnectedMonitors(self, outputs = None):
        if outputs is None:
            outputs = self.findConnectedMonitorMatchObjects()
        outputNames = []
        for output in outputs:
            # if output.group("connection") == "connected":
            outputNames.append(output.group("outputName"))
        return outputNames

    def findConnectedMonitorMatchObjects(self):
        outputs = [x for x in self.outputRegex.finditer(self.xrandrOutput)]
        return outputs

    def findActiveMonitors(self):
        outputs = self.findConnectedMonitorMatchObjects()
        activeMonitors = []
        for output in outputs:
            substring = self.cutOutputSubstring(output, self.xrandrOutput)
            for resolution in self.resolutionRegex.finditer(substring):
                if resolution.group("active") == '*':
                    activeMonitors.append(output.group('outputName'))
        return activeMonitors

    def findPreferredResolutionForMonitor(self, monitorName):
        for output in self.findConnectedMonitorMatchObjects():
            outputName = output.group('outputName')
            if outputName == monitorName:
                substring = self.cutOutputSubstring(output, self.xrandrOutput)
                resolutions = [x for x in self.resolutionRegex.finditer(substring)]
                for resolution in resolutions:
                    if resolution.group('preferred') != '':
                        preferredResolution = resolution.group('resolution')
                        return self.makeResolutionDict(preferredResolution)
                preferredResolution = resolutions[0].group('resolution')
                return self.makeResolutionDict(preferredResolution)

    def cutOutputSubstring(self, currentOutput, substring):
        nextOutput = self.outputRegex.search(substring[currentOutput.end():])
        if nextOutput is not None:
            end = nextOutput.end()
        else:
            end = -1
        substring = substring[currentOutput.end():end]
        return substring

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
        for output in self.findConnectedMonitorMatchObjects():
            outputName = output.group('outputName')
            for monitor in monitors:
                if monitor == outputName:
                    substring = self.cutOutputSubstring(output, self.xrandrOutput)
                    monitorResolutions[outputName] = {x.group('resolution') for x in self.resolutionRegex.finditer(substring)}
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
            if position is None:
                position = '0x0'
            positionArgument = ['--pos', position]
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

    def internal(self):
        arguments = [
                self.makeArgumentList(self.defaultMonitor)
                ]
        for monitor in self.findConnectedMonitors():
            if monitor != self.defaultMonitor:
                arguments.append(self.makeArgumentList(monitor, off=True))
        self.setCommand(arguments)
        self.setLayout()

    def toggle(self):
        additionalMonitor = self.findFirstAdditionalMonitor()
        activeMonitors = self.findActiveMonitors()
        if self.defaultMonitor in activeMonitors:
            if additionalMonitor in activeMonitors:
                self.external()
            else:
                self.clone()
        else:
            self.internal()

if __name__ == "__main__":
    l = Layout('LVDS1')
    l.setBelowMiddle()
