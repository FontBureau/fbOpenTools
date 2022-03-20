from mojo.subscriber import getRegisteredSubscriberEvents, registerSubscriberEvent

DEBUG_MODE = False
DEFAULTKEY = "com.fontbureau.overlayUFO"


def subscriberEventGlyphExtractor(subscriber, info):
    info["glyph"] = []
    for lowLevelEvent in info["lowLevelEvents"]:
        info["glyph"] = lowLevelEvent["glyph"]


def contextEventPositionExtractor(subscriber, info):
    info["position"] = []
    for lowLevelEvent in info["lowLevelEvents"]:
        info["position"] = lowLevelEvent["position"]


customEvents = {
    "openedFontsDidChange": "update signal from the fontsmanager to the main controller",
    "alignmentDidChange": "update signal from the controller to the glyph subscriber",
    "displayedFontsDidChange": "update signal from the controller to the glyph subscriber",
    "contextDidChange": "update signal from the controller to the glyph subscriber",
    "fillCheckBoxDidChange": "update signal from the controller to the glyph subscriber",
    "strokeCheckBoxDidChange": "update signal from the controller to the glyph subscriber",
    "colorDidChange": "update signal from the controller to the glyph subscriber",
    "alwaysCurrentViewDidChange": "update signal from the controller to the glyph subscriber",
    "fontListDidChange": "update signal from the controller to the glyph subscriber",
    "displayedGlyphDidChange": "update signal from the current glyph subscriber to the glyph subscriber",
}

eventNameToExtractorFunc = {
    "displayedGlyphDidChange": subscriberEventGlyphExtractor,
    "contextDidChange": contextEventPositionExtractor,
}

if __name__ == "__main__":
    subscriberEvents = getRegisteredSubscriberEvents()
    for methodName, docstring in customEvents.items():
        eventName = f"{DEFAULTKEY}.{methodName}"
        if eventName not in subscriberEvents:
            registerSubscriberEvent(
                subscriberEventName=eventName,
                methodName=methodName,
                lowLevelEventNames=[eventName],
                documentation=docstring,
                eventInfoExtractionFunction=eventNameToExtractorFunc.get(methodName),
                dispatcher="roboFont",
                delay=0.1,
                debug=DEBUG_MODE,
            )
