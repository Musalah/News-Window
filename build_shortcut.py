#!/usr/bin/env python3
"""Generate the unsigned "نافذة الأخبار" .shortcut plist.

Usage: python3 build_shortcut.py [output_path]
"""
import plistlib
import sys
import uuid

ACCOUNTS = [
    "https://www.snapchat.com/@trendnews24",
    "https://www.snapchat.com/@saudi.panther",
]
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)
NEXT_DATA_PATTERN = r"(?s)__NEXT_DATA__[^>]*>(.*?)</script>"
SNAP_LIST_PATH = "props.pageProps.story.snapList"
MEDIA_URL_PATH = "snapUrls.mediaUrl"
VARIABLE = "Stories"


def uid():
    return str(uuid.uuid4()).upper()


def output_ref(action_uuid, name):
    return {"Type": "ActionOutput", "OutputUUID": action_uuid, "OutputName": name}


def variable_ref(name):
    return {"Type": "Variable", "VariableName": name}


def attachment(ref):
    return {"Value": ref, "WFSerializationType": "WFTextTokenAttachment"}


def token_string(ref):
    return {
        "Value": {"string": "￼", "attachmentsByRange": {"{0, 1}": ref}},
        "WFSerializationType": "WFTextTokenString",
    }


def plain_text(s):
    return {"Value": {"string": s}, "WFSerializationType": "WFTextTokenString"}


def action(identifier, **params):
    return {"WFWorkflowActionIdentifier": f"is.workflow.actions.{identifier}",
            "WFWorkflowActionParameters": params}


def has_value_condition(ref):
    return {"Type": "Variable", "Variable": attachment(ref)}


def download(url_ref, out_uuid, headers=True):
    params = {"UUID": out_uuid, "WFURL": token_string(url_ref), "WFHTTPMethod": "GET"}
    if headers:
        params["ShowHeaders"] = True
        params["WFHTTPHeaders"] = {
            "Value": {"WFDictionaryFieldValueItems": [{
                "WFItemType": 0,
                "WFKey": plain_text("User-Agent"),
                "WFValue": plain_text(USER_AGENT),
            }]},
            "WFSerializationType": "WFDictionaryFieldValue",
        }
    return action("downloadurl", **params)


def build():
    list_id, page_id, match_id, group_id, dict_id, snaps_id, media_id, file_id = (
        uid() for _ in range(8))
    outer, inner, has_snaps, has_stories = uid(), uid(), uid(), uid()

    actions = [
        action("list", UUID=list_id, WFItems=ACCOUNTS),
        action("repeat.each", GroupingIdentifier=outer, WFControlFlowMode=0,
               WFInput=attachment(output_ref(list_id, "List"))),
        download(variable_ref("Repeat Item"), page_id),
        action("text.match", UUID=match_id, WFMatchTextPattern=NEXT_DATA_PATTERN,
               WFMatchTextCaseSensitive=True,
               text=token_string(output_ref(page_id, "Contents of URL"))),
        action("text.match.getgroup", UUID=group_id, WFGetGroupType="Group At Index",
               WFGroupIndex=1, matches=attachment(output_ref(match_id, "Matches"))),
        action("detect.dictionary", UUID=dict_id,
               WFInput=attachment(output_ref(group_id, "Text"))),
        action("getvalueforkey", UUID=snaps_id, WFGetDictionaryValueType="Value",
               WFDictionaryKey=SNAP_LIST_PATH,
               WFInput=attachment(output_ref(dict_id, "Dictionary"))),
        # Account without a story: snapList is missing, so skip it quietly.
        action("conditional", GroupingIdentifier=has_snaps, WFControlFlowMode=0,
               WFCondition=100,
               WFInput=has_value_condition(output_ref(snaps_id, "Dictionary Value"))),
        action("repeat.each", GroupingIdentifier=inner, WFControlFlowMode=0,
               WFInput=attachment(output_ref(snaps_id, "Dictionary Value"))),
        action("getvalueforkey", UUID=media_id, WFGetDictionaryValueType="Value",
               WFDictionaryKey=MEDIA_URL_PATH,
               WFInput=attachment(variable_ref("Repeat Item 2"))),
        download(output_ref(media_id, "Dictionary Value"), file_id, headers=False),
        action("appendvariable", WFVariableName=VARIABLE,
               WFInput=attachment(output_ref(file_id, "Contents of URL"))),
        action("repeat.each", GroupingIdentifier=inner, WFControlFlowMode=2),
        action("conditional", GroupingIdentifier=has_snaps, WFControlFlowMode=2),
        action("repeat.each", GroupingIdentifier=outer, WFControlFlowMode=2),
        action("conditional", GroupingIdentifier=has_stories, WFControlFlowMode=0,
               WFCondition=100,
               WFInput=has_value_condition(variable_ref(VARIABLE))),
        action("previewdocument", WFInput=attachment(variable_ref(VARIABLE))),
        action("conditional", GroupingIdentifier=has_stories, WFControlFlowMode=1),
        action("notification", WFNotificationActionTitle="نافذة الأخبار",
               WFNotificationActionBody="لا توجد قصص حالياً"),
        action("conditional", GroupingIdentifier=has_stories, WFControlFlowMode=2),
    ]

    return {
        "WFWorkflowActions": actions,
        "WFWorkflowClientVersion": "2302.0.4",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983,
                           "WFWorkflowIconGlyphNumber": 59511},
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": [],
        "WFWorkflowHasShortcutInputVariables": False,
        "WFQuickActionSurfaces": [],
    }


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "news-window.unsigned.shortcut"
    with open(out, "wb") as f:
        plistlib.dump(build(), f, fmt=plistlib.FMT_BINARY)
    print(out)
