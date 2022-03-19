from mojo.subscriber import getRegisteredSubscriberEvents, registerSubscriberEvent

DEBUG_MODE = True
DEFAULTKEY = "com.fontbureau.overlayUFO"

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
    "editorGlyphDidChange": "update signal from the current glyph subscriber to the glyph subscriber",
    "contextGlyphDidChange": "update signal from the current glyph subscriber to the glyph subscriber",
}


def subscriberEventGlyphExtractor(subscriber, info):
    info["glyph"] = []
    for lowLevelEvent in info["lowLevelEvents"]:
        info["glyph"] = lowLevelEvent["glyph"]


if __name__ == "__main__":
    subscriberEvents = getRegisteredSubscriberEvents()
    for methodName, docstring in customEvents.items():

        extractionFunc = (
            subscriberEventGlyphExtractor if methodName in ["editorGlyphDidChange", "contextGlyphDidChange"] else None
        )
        eventName = f"{DEFAULTKEY}.{methodName}"
        if eventName not in subscriberEvents:
            registerSubscriberEvent(
                subscriberEventName=eventName,
                methodName=methodName,
                lowLevelEventNames=[eventName],
                documentation=docstring,
                eventInfoExtractionFunction=extractionFunc,
                dispatcher="roboFont",
                delay=0.1,
                debug=DEBUG_MODE,
            )
