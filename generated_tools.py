
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP, Context

# Assumes 'mcp' object is available in the exec context or we import it here if running standalone
# But for dynamic loading, we might rely on the server's context. 
# Best practice: make tools standalone-ish or accept a session.


# Tool for https://trello.com/1/board/697e3746ad617b8629cef437?fields=id&accessRequests=true
@mcp.tool()
async def get_trello_board_access_requests(board_id: str):
    """
    Retrieves pending access requests for a specific Trello board.
    
    This tool queries the Trello API for a board's ID and its current list of access requests, 
    which is useful for managing board permissions and identifying users who want to join.
    
    Args:
        board_id: The unique identifier for the Trello board (e.g., '697e3746ad617b8629cef437').
    """
    url = f"https://trello.com/1/board/{board_id}"
    params = {
        "fields": "id",
        "accessRequests": "true"
    }
    headers = {
        "x-trello-operation-name": "BoardAccessRequests",
        "x-trello-operation-source": "graphql",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code}", "details": e.response.text}
        except httpx.RequestError as e:
            return {"error": f"An error occurred while requesting {e.request.url!r}: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://trello.com/1/boards/697e3746ad617b8629cef437/markAsViewed
@mcp.tool()
async def mark_board_as_viewed(board_id: str, dsc: str) -> str:
    """
    Marks a Trello board as viewed for the current user session.

    Args:
        board_id (str): The unique identifier of the Trello board.
        dsc (str): The security/session token (dsc) required by Trello's internal API.
    """
    url = f"https://trello.com/1/boards/{board_id}/markAsViewed"
    
    headers = {
        "x-requested-with": "XMLHttpRequest",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-trello-client-version": "build-231871",
        "accept": "*/*"
    }
    
    data = {
        "dsc": dsc
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, data=data)
            response.raise_for_status()
            # Return text as the response might be an empty string or simple confirmation
            return response.text if response.text else "Success: Board marked as viewed."
        except httpx.HTTPStatusError as e:
            return f"HTTP Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://atlassian-cookies--categories.us-east-1.prod.public.atl-paas.net/categories_COOKIE.json
@mcp.tool()
async def get_atlassian_cookie_categories() -> dict | str:
    """
    Fetches the cookie category definitions for Atlassian services such as Trello.

    This tool retrieves the official JSON configuration that defines various cookie 
    categories (e.g., essential, analytics, functional) used across Atlassian's 
    infrastructure. This is useful for privacy auditing and understanding data 
    collection practices.

    Returns:
        dict: The JSON object containing cookie category definitions if successful.
        str: An error message detailing the failure if the request fails.
    """
    url = "https://atlassian-cookies--categories.us-east-1.prod.public.atl-paas.net/categories_COOKIE.json"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting the URL: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/gateway/api/graphql?operationName=quickload:TrelloCurrentBoardInfo
@mcp.tool()
async def get_trello_board_info(short_link: str) -> dict:
    """
    Retrieves detailed board information from Trello using its short link.
    
    This tool uses Trello's GraphQL gateway to fetch a comprehensive snapshot of a board, 
    including its members, labels, lists, custom fields, power-up data, and workspace context.
    
    Args:
        short_link: The short link ID of the Trello board (e.g., 'a7UxwGZY').
    """
    url = "https://trello.com/gateway/api/graphql"
    params = {"operationName": "quickload:TrelloCurrentBoardInfo"}
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "x-trello-operation-name": "quickload:TrelloCurrentBoardInfo",
        "x-trello-operation-source": "quickload",
        "referer": f"https://trello.com/b/{short_link}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }
    
    query = """query TrelloCurrentBoardInfo($id:TrelloShortLink!){trello{__typename boardByShortLink(shortLink:$id)@optIn(to:\"TrelloBoard\"){id __typename closed creationMethod creator{id __typename objectId}customFields{__typename edges{__typename node{id __typename display{__typename cardFront}name objectId options{__typename color objectId position value{__typename text}}position type}}}description{__typename text}enterprise{id __typename displayName objectId}enterpriseOwned galleryInfo{id __typename avatarShape avatarUrl blurb byline category{__typename key}featured language{__typename description enabled language locale localizedDescription}precedence stats{__typename copyCount viewCount}}labels(first:-1){__typename edges{__typename node{id __typename color name objectId}}}lastActivityAt limits{__typename attachments{__typename perBoard{__typename disableAt status warnAt}perCard{__typename disableAt status warnAt}}boards{__typename totalMembersPerBoard{__typename disableAt status warnAt}}cards{__typename openPerBoard{__typename disableAt status warnAt}openPerList{__typename disableAt status warnAt}totalPerBoard{__typename disableAt status warnAt}totalPerList{__typename disableAt status warnAt}}checkItems{__typename perChecklist{__typename disableAt status warnAt}}checklists{__typename perBoard{__typename disableAt status warnAt}perCard{__typename disableAt status warnAt}}customFieldOptions{__typename perField{__typename disableAt status warnAt}}customFields{__typename perBoard{__typename disableAt status warnAt}}labels{__typename perBoard{__typename disableAt status warnAt}}lists{__typename openPerBoard{__typename disableAt status warnAt}totalPerBoard{__typename disableAt status warnAt}}reactions{__typename perAction{__typename disableAt status warnAt}uniquePerAction{__typename disableAt status warnAt}}stickers{__typename perCard{__typename disableAt status warnAt}}}members(first:-1){__typename edges{__typename membership{__typename deactivated objectId type unconfirmed workspaceMemberType}node{id __typename activityBlocked avatarUrl bio bioData confirmed enterprise{id __typename objectId}fullName initials nonPublicData{__typename avatarUrl fullName initials}objectId url username}}}name objectId powerUpData(first:-1){__typename edges{__typename node{id __typename access objectId powerUp{__typename objectId}scope value}}}powerUps(filter:{access:\"enabled\"},first:-1){__typename edges{__typename node{__typename objectId}objectId}}prefs{__typename background{__typename bottomColor brightness color image imageScaled{__typename height url width}tile topColor}calendarFeedEnabled canInvite cardAging cardCounts cardCovers comments hiddenPowerUpBoardButtons{__typename objectId}hideVotes invitations isTemplate permissionLevel selfJoin showCompleteStatus switcherViews{__typename enabled viewType}voting}premiumFeatures shortLink shortUrl tags(first:-1){__typename edges{__typename node{__typename objectId}}}url viewer{__typename calendarKey email{__typename key list{id __typename objectId}position}lastSeenAt sidebar{__typename show}subscribed}workspace{id __typename description displayName enterprise{id __typename admins(first:-1){__typename edges{__typename node{id __typename}}}displayName objectId}limits{__typename freeBoards{__typename disableAt status warnAt}freeCollaborators{__typename disableAt status warnAt}totalMembers{__typename disableAt status warnAt}}logoHash members(first:-1){__typename edges{__typename membership{__typename deactivated objectId type unconfirmed}node{id __typename objectId}}}name objectId offering prefs{__typename associatedDomain attachmentRestrictions boardDeleteRestrict{__typename enterprise org private public}boardInviteRestrict boardVisibilityRestrict{__typename enterprise org private public}externalMembersDisabled orgInviteRestrict permissionLevel}products tags(first:-1){__typename edges{__typename node{__typename name objectId}}}url website}}}}"""
    
    payload = {
        "query": query,
        "variables": {"id": short_link},
        "operationName": "TrelloCurrentBoardInfo"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": "Trello API returned an error",
                "status_code": e.response.status_code,
                "response": e.response.text
            }
        except Exception as e:
            return {"error": str(e)}


# Tool for https://trello.com/gateway/api/graphql?operationName=quickload:TrelloMemberBoards
@mcp.tool()
async def get_trello_member_boards():
    """
    Retrieves the current Trello member's profile information and starred boards.
    
    This tool queries Trello's GraphQL gateway to fetch account details including the 
    member's ID, username, and metadata for boards they have marked as favorites (starred), 
    such as board object IDs and their display positions.
    
    Returns:
        dict: The JSON response containing member and board star data, or an error object if the request fails.
    """
    url = "https://trello.com/gateway/api/graphql?operationName=quickload:TrelloMemberBoards"
    
    headers = {
        "x-trello-operation-name": "quickload:TrelloMemberBoards",
        "x-trello-operation-source": "quickload",
        "x-trello-client-version": "build-231871",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "referer": "https://trello.com/b/a7UxwGZY/testboard"
    }
    
    payload = {
        "query": "query TrelloMemberBoards{trello{__typename me@optIn(to:\"TrelloMe\"){id __typename boardStars{__typename edges{id __typename boardObjectId objectId position}}objectId username}}}",
        "variables": {},
        "operationName": "TrelloMemberBoards"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": "HTTP request failed",
            "status_code": e.response.status_code,
            "details": e.response.text
        }
    except httpx.RequestError as e:
        return {
            "error": "A network error occurred while contacting Trello",
            "details": str(e)
        }
    except Exception as e:
        return {
            "error": "An unexpected error occurred",
            "details": str(e)
        }


# Tool for https://trello.com/1/board/a7UxwGZY?fields=id&cards=visible&card_fields=id%2Caddress%2Cagent%2Cbadges%2CcardRole%2Cclosed%2Ccoordinates%2Ccover%2CcreationMethod%2CcreationMethodError%2CcreationMethodLoadingStartedAt%2CdateLastActivity%2Cdesc%2CdescData%2Cdue%2CdueComplete%2CdueReminder%2CfaviconUrl%2CidAttachmentCover%2CidBoard%2CidLabels%2CidList%2CidMembers%2CidShort%2CisTemplate%2Clabels%2Climits%2ClocationName%2CmirrorSourceId%2Cname%2CnodeId%2CoriginalDesc%2CoriginalName%2Cpinned%2Cpos%2CrecurrenceRule%2CshortLink%2CshortUrl%2CsingleInstrumentationId%2Cstart%2Csubscribed%2Curl%2CurlSource%2CurlSourceText&card_attachments=true&card_attachment_fields=id%2Cbytes%2Cdate%2CedgeColor%2CfileName%2CidMember%2CisMalicious%2CisUpload%2CmimeType%2Cname%2Cpos%2Curl&card_checklists=all&card_checklist_fields=id%2CidBoard%2CidCard%2Cname%2Cpos&card_checklist_checkItems=none&card_customFieldItems=true&card_pluginData=true&card_stickers=true&lists=open&list_fields=id%2Cclosed%2Ccolor%2CcreationMethod%2Cdatasource%2CidBoard%2Climits%2Cname%2CnodeId%2Cpos%2CsoftLimit%2Csubscribed%2Ctype&operationName=quickload:CurrentBoardListsCards
@mcp.tool()
async def get_trello_board_details(board_id: str, api_key: str, token: str) -> dict:
    """
    Fetches a comprehensive view of a Trello board, including lists, cards, attachments, 
    checklists, and custom field data. This is optimized for a full board "quickload".

    Args:
        board_id: The shortLink or ID of the Trello board to retrieve.
        api_key: Your Trello API key.
        token: Your Trello API token.
    """
    url = f"https://trello.com/1/board/{board_id}"
    
    params = {
        "key": api_key,
        "token": token,
        "fields": "id",
        "cards": "visible",
        "card_fields": "id,address,agent,badges,cardRole,closed,coordinates,cover,creationMethod,creationMethodError,creationMethodLoadingStartedAt,dateLastActivity,desc,descData,due,dueComplete,dueReminder,faviconUrl,idAttachmentCover,idBoard,idLabels,idList,idMembers,idShort,isTemplate,labels,limits,locationName,mirrorSourceId,name,nodeId,originalDesc,originalName,pinned,pos,recurrenceRule,shortLink,shortUrl,singleInstrumentationId,start,subscribed,url,urlSource,urlSourceText",
        "card_attachments": "true",
        "card_attachment_fields": "id,bytes,date,edgeColor,fileName,idMember,isMalicious,isUpload,mimeType,name,pos,url",
        "card_checklists": "all",
        "card_checklist_fields": "id,idBoard,idCard,name,pos",
        "card_checklist_checkItems": "none",
        "card_customFieldItems": "true",
        "card_pluginData": "true",
        "card_stickers": "true",
        "lists": "open",
        "list_fields": "id,closed,color,creationMethod,datasource,idBoard,limits,name,nodeId,pos,softLimit,subscribed,type",
        "operationName": "quickload:CurrentBoardListsCards"
    }
    
    headers = {
        "accept": "application/json,text/plain",
        "x-trello-operation-name": "quickload:CurrentBoardListsCards",
        "x-trello-operation-source": "quickload"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"Trello API returned error {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://trello.com/gateway/api/graphql?operationName=quickload:TrelloBoardMirrorCards
@mcp.tool()
async def get_trello_board_mirror_cards(board_id: str, first: int = 50, after: str = None):
    """
    Retrieves mirror cards for a specific Trello board using the Trello GraphQL gateway.
    
    Mirror cards are synchronized copies of cards from other boards. This tool fetches 
    comprehensive information about these mirrors, including their source board details 
    (workspace, custom fields, labels, power-ups), source card details (attachments, 
    checklists, due dates, custom field items, members), and their current status on 
    the target board.

    Args:
        board_id: The short link or ID of the Trello board (e.g., 'a7UxwGZY').
        first: The number of items to retrieve (pagination limit, default: 50).
        after: The cursor for pagination to fetch the next set of results.
    """
    url = "https://trello.com/gateway/api/graphql"
    params = {"operationName": "quickload:TrelloBoardMirrorCards"}
    
    query = """
    query TrelloBoardMirrorCards($id: TrelloShortLink!, $after: String, $first: Int = 50) {
      trello {
        __typename
        boardMirrorCardInfo(shortLink: $id) @optIn(to: "TrelloBoardMirrorCardInfo") {
          id
          __typename
          mirrorCards(after: $after, first: $first) {
            __typename
            edges {
              __typename
              node {
                id
                __typename
                mirrorCard {
                  id
                  __typename
                }
                sourceBoard {
                  id
                  __typename
                  closed
                  customFields {
                    __typename
                    edges {
                      __typename
                      node {
                        id
                        __typename
                        display {
                          __typename
                          cardFront
                        }
                        name
                        objectId
                        options {
                          __typename
                          color
                          objectId
                          position
                          value {
                            __typename
                            text
                          }
                        }
                        position
                        type
                      }
                    }
                  }
                  enterprise {
                    id
                    __typename
                    objectId
                  }
                  labels(first: -1) {
                    __typename
                    edges {
                      __typename
                      node {
                        id
                        __typename
                        color
                        name
                        objectId
                      }
                    }
                  }
                  name
                  objectId
                  powerUps {
                    __typename
                    edges {
                      __typename
                      node {
                        __typename
                        objectId
                      }
                      objectId
                    }
                  }
                  prefs {
                    __typename
                    background {
                      __typename
                      brightness
                      color
                      image
                      imageScaled {
                        __typename
                        height
                        url
                        width
                      }
                      tile
                      topColor
                    }
                    cardAging
                    cardCovers
                    showCompleteStatus
                  }
                  shortLink
                  url
                  workspace {
                    id
                    __typename
                    objectId
                  }
                }
                sourceCard {
                  id
                  __typename
                  attachments(first: -1) {
                    __typename
                    edges {
                      __typename
                      node {
                        id
                        __typename
                        isMalicious
                        objectId
                      }
                    }
                  }
                  badges {
                    __typename
                    attachments
                    attachmentsByType {
                      __typename
                      trello {
                        __typename
                        board
                        card
                      }
                    }
                    checkItems
                    checkItemsChecked
                    checkItemsEarliestDue
                    comments
                    description
                    due {
                      __typename
                      at
                      complete
                    }
                    externalSource
                    lastUpdatedByAi
                    location
                    maliciousAttachments
                    startedAt
                    viewer {
                      __typename
                      subscribed
                      voted
                    }
                    votes
                  }
                  checklists(first: -1) {
                    __typename
                    edges {
                      __typename
                      node {
                        id
                        __typename
                        objectId
                      }
                    }
                  }
                  closed
                  complete
                  cover {
                    __typename
                    attachment {
                      id
                      __typename
                      objectId
                    }
                    brightness
                    color
                    edgeColor
                    powerUp {
                      __typename
                      objectId
                    }
                    previews {
                      __typename
                      edges {
                        __typename
                        node {
                          __typename
                          bytes
                          height
                          objectId
                          scaled
                          url
                          width
                        }
                      }
                    }
                    sharedSourceUrl
                    size
                    uploadedBackground {
                      __typename
                      objectId
                    }
                    yPosition
                  }
                  creation {
                    __typename
                    loadingStartedAt
                    method
                  }
                  customFieldItems(first: -1) {
                    __typename
                    edges {
                      __typename
                      node {
                        __typename
                        customField {
                          id
                          __typename
                          objectId
                        }
                        objectId
                        value {
                          __typename
                          checked
                          date
                          number
                          objectId
                          text
                        }
                      }
                    }
                  }
                  description {
                    __typename
                    text
                  }
                  due {
                    __typename
                    at
                    reminder
                  }
                  isTemplate
                  labels(first: -1) {
                    __typename
                    edges {
                      __typename
                      node {
                        id
                        __typename
                        color
                        name
                        objectId
                      }
                    }
                  }
                  lastActivityAt
                  limits {
                    __typename
                    stickers {
                      __typename
                      perCard {
                        __typename
                        disableAt
                      }
                    }
                  }
                  list @optIn(to: "TrelloListBoard") {
                    id
                    __typename
                    board {
                      id
                      __typename
                      objectId
                    }
                    closed
                    name
                    objectId
                    position
                    softLimit
                  }
                  location {
                    __typename
                    address
                    coordinates {
                      __typename
                      latitude
                      longitude
                    }
                    name
                    staticMapUrl
                  }
                  members(first: -1) {
                    __typename
                    edges {
                      __typename
                      node {
                        id
                        __typename
                        avatarUrl
                        fullName
                        initials
                        nonPublicData {
                          __typename
                          avatarUrl
                          fullName
                          initials
                        }
                        objectId
                        username
                      }
                    }
                  }
                  mirrorSourceId
                  mirrorSourceNodeId
                  name
                  objectId
                  pinned
                  powerUpData {
                    __typename
                    edges {
                      __typename
                      node {
                        id
                        __typename
                        objectId
                        powerUp {
                          __typename
                          objectId
                        }
                        value
                      }
                    }
                  }
                  role
                  shortId
                  shortLink
                  singleInstrumentationId
                  stickers(first: -1) {
                    __typename
                    edges {
                      __typename
                      node {
                        __typename
                        image
                        imageScaled {
                          __typename
                          height
                          objectId
                          scaled
                          url
                          width
                        }
                        left
                        objectId
                        rotate
                        top
                        url
                        zIndex
                      }
                    }
                  }
                  url
                }
              }
            }
            pageInfo {
              __typename
              endCursor
              hasNextPage
            }
          }
        }
      }
    }
    """
    
    variables = {
        "id": board_id,
        "after": after,
        "first": first
    }
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "accept": "application/json",
        "x-trello-operation-name": "quickload:TrelloBoardMirrorCards",
        "x-trello-operation-source": "quickload",
        "x-trello-task": "view-board"
    }
    
    payload = {
        "query": query,
        "variables": variables,
        "operationName": "TrelloBoardMirrorCards"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": "HTTP error occurred", "status_code": e.response.status_code, "message": e.response.text}
        except Exception as e:
            return {"error": "An unexpected error occurred", "message": str(e)}


# Tool for https://trello.com/gateway/api/graphql?operationName=quickload:TrelloCurrentBoardListsCards
@mcp.tool()
async def get_trello_board_lists_and_cards(short_link: str):
    """
    Fetches the lists and cards of a Trello board by its short link using the Trello GraphQL API.
    
    This tool retrieves board details including list IDs, card IDs, labels, and closed status.
    
    Args:
        short_link (str): The short link ID of the board (e.g., 'a7UxwGZY').
    """
    url = "https://trello.com/gateway/api/graphql"
    
    headers = {
        "x-trello-operation-name": "quickload:TrelloCurrentBoardListsCards",
        "x-trello-operation-source": "quickload",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }
    
    query = """
    query TrelloCurrentBoardListsCards($id:TrelloShortLink!){
      trello{
        __typename 
        boardByShortLink(shortLink:$id)@optIn(to:"TrelloBoard"){
          id 
          __typename 
          lists(first:-1){
            __typename 
            edges{
              __typename 
              node{
                id 
                __typename 
                cards(first:-1)@optIn(to:"TrelloListCards"){
                  __typename 
                  edges{
                    __typename 
                    node{
                      id 
                      __typename 
                      closed 
                      labels(first:-1){
                        __typename 
                        edges{
                          __typename 
                          node{
                            id 
                            __typename 
                            color 
                            name 
                            objectId
                          }
                        }
                      }
                      objectId
                      ...on TrelloCard{
                        isTemplate
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    payload = {
        "query": query,
        "variables": {"id": short_link},
        "operationName": "TrelloCurrentBoardListsCards"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://o55978.ingest.sentry.io/api/5988847/envelope/?sentry_version=7&sentry_key=1609e814bfa14a3db09f984e6426cfd3&sentry_client=sentry.javascript.browser%2F10.34.0
@mcp.tool()
async def post_sentry_envelope(
    project_id: str = "5988847",
    sentry_key: str = "1609e814bfa14a3db09f984e6426cfd3",
    sentry_version: str = "7",
    sentry_client: str = "sentry.javascript.browser/10.34.0",
    envelope_data: str = '{"sent_at":"2026-02-01T06:34:15.605Z","sdk":{"name":"sentry.javascript.browser","version":"10.34.0"}}\n{"type":"session"}\n{"sid":"b686fbeab2f3425cb6631fba1c189716","init":true,"started":"2026-02-01T06:34:15.605Z","timestamp":"2026-02-01T06:34:15.605Z","status":"ok","errors":0,"attrs":{"release":"build-231871","environment":"prod","user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"}}'
) -> str:
    """
    Sends a telemetry envelope to Sentry ingest API.
    
    This tool transmits session, event, or error data to Sentry using the envelope format.
    It is specifically configured for Sentry's ingestion endpoint, including the necessary 
    authentication keys and client version information.

    Args:
        project_id: The specific Sentry project identifier.
        sentry_key: The authentication key (DSN public key) for the Sentry project.
        sentry_version: The version of the Sentry protocol being used.
        sentry_client: The identifier for the Sentry SDK client.
        envelope_data: The multi-line string containing the envelope headers and items.
    """
    url = f"https://o55978.ingest.sentry.io/api/{project_id}/envelope/"
    
    params = {
        "sentry_version": sentry_version,
        "sentry_key": sentry_key,
        "sentry_client": sentry_client
    }
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain;charset=UTF-8",
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                params=params,
                headers=headers,
                content=envelope_data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.text if response.text else "Envelope successfully sent (No response body)."
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while sending envelope: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting {e.request.url!r}: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://atlassian-cookies--categories.us-east-1.prod.public.atl-paas.net/categories_COOKIE.json
@mcp.tool()
async def get_atlassian_cookie_categories() -> dict | str:
    """
    Fetches the cookie categorization data from Atlassian's public configuration.

    This tool retrieves the JSON definitions for cookie categories (such as necessary, performance, 
    functional, and advertising cookies) used by Atlassian services like Trello. It is useful 
    for auditing tracking behavior or understanding privacy policy implementations.

    Returns:
        dict: The parsed JSON content containing cookie categories and their descriptions.
        str: An error message if the request fails.
    """
    url = "https://atlassian-cookies--categories.us-east-1.prod.public.atl-paas.net/categories_COOKIE.json"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while fetching cookie categories: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"A request error occurred while fetching cookie categories: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/gateway/api/gasv3/api/v1/metadata?product=trello&userId=&userIdType=&tenantId=&tenantIdType=
@mcp.tool()
async def get_trello_metadata(
    product: str = "trello",
    user_id: str = "",
    user_id_type: str = "",
    tenant_id: str = "",
    tenant_id_type: str = ""
) -> dict | str:
    """
    Retrieves environment and session metadata from Trello's internal gateway API.

    This tool fetches metadata used by the Trello web application for analytics and session context,
    including product details, user identification, and tenant configurations.

    Args:
        product: The name of the product (e.g., 'trello').
        user_id: The unique identifier for the user, if available.
        user_id_type: The type or category of the user identifier.
        tenant_id: The unique identifier for the tenant or workspace.
        tenant_id_type: The type or category of the tenant identifier.
    """
    url = "https://trello.com/gateway/api/gasv3/api/v1/metadata"
    params = {
        "product": product,
        "userId": user_id,
        "userIdType": user_id_type,
        "tenantId": tenant_id,
        "tenantIdType": tenant_id_type
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            try:
                return response.json()
            except Exception:
                return response.text
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"A request error occurred while accessing {e.request.url}: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/assets/detect-gpu/5.0.70/d-intel.json
@mcp.tool()
async def get_trello_gpu_intel_config():
    """
    Retrieves GPU detection configuration data for Intel graphics processors from Trello's static assets.
    
    This tool fetches a specific JSON asset used by Trello to determine hardware capabilities 
    and optimize client-side rendering for Intel-based systems.
    
    Returns:
        dict: The parsed JSON data containing hardware detection parameters or an error message.
    """
    url = "https://trello.com/assets/detect-gpu/5.0.70/d-intel.json"
    headers = {
        'sec-ch-ua-platform': '"Windows"',
        'referer': 'https://trello.com/b/a7UxwGZY/testboard',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting {e.request.url!r}: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://api.atlassian.com/flags/api/v2/frontend/clientSdkKey/trello_web
@mcp.tool()
async def get_trello_frontend_feature_flags() -> dict | str:
    """
    Retrieves frontend feature flags and configuration for Trello web from the Atlassian flags API.
    
    This tool interacts with the Atlassian Feature Gate service to fetch current feature flag 
    evaluations and client configurations for the Trello web application.
    """
    url = "https://api.atlassian.com/flags/api/v2/frontend/clientSdkKey/trello_web"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "x-api-key": "1f24403e-f053-43de-b063-e20b357a8f63",
        "sec-ch-ua-mobile": "?0",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-client-version": "0.0.0-development",
        "x-client-name": "feature-gate-js-client",
        "content-type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while fetching feature flags: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting feature flags: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://api.atlassian.com/flags/api/v2/frontend/experimentValues
@mcp.tool()
async def get_trello_experiment_values(
    atlassian_account_id: str = "712020:8d77ca7f-09f0-4b38-92cf-94b7270b5a34",
    analytics_anonymous_id: str = "e6e6a109-d7ef-4ad5-8f64-b4a7f1e93aa5",
    target_app: str = "trello_web",
    locale: str = "en-US"
) -> dict:
    """
    Fetches feature flag experiment values and configuration for Trello web interface.
    This tool interacts with the Atlassian Flags API to determine which features/experiments 
    are active for a specific user session.

    Args:
        atlassian_account_id: The unique identifier for the Atlassian account.
        analytics_anonymous_id: The anonymous ID used for tracking and experiment assignment.
        target_app: The application platform identifier (e.g., 'trello_web').
        locale: The user's locale string.
    """
    url = "https://api.atlassian.com/flags/api/v2/frontend/experimentValues"
    
    headers = {
        "x-api-key": "1f24403e-f053-43de-b063-e20b357a8f63",
        "x-client-name": "feature-gate-js-client",
        "x-client-version": "0.0.0-development",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "referer": "https://trello.com/"
    }

    payload = {
        "identifiers": {
            "atlassianAccountId": atlassian_account_id,
            "analyticsAnonymousId": analytics_anonymous_id
        },
        "customAttributes": {
            "inEnterprise": False,
            "version": 231871,
            "locale": locale,
            "isDesktop": False,
            "isTouch": False,
            "idEnterprises": [],
            "signupDate": 1769875257000,
            "channel": "main",
            "isPremium": False,
            "isStandard": False,
            "hasMultipleEmails": False,
            "userCohortPersonalProductivity": "ga",
            "userCohortReferralPilot": "not_set",
            "inRealEnterprise": False,
            "hasEnterpriseDomain": False
        },
        "targetApp": target_app
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": "HTTP error occurred while fetching experiment values",
            "status_code": e.response.status_code,
            "message": e.response.text
        }
    except Exception as e:
        return {
            "error": "An unexpected error occurred",
            "details": str(e)
        }


# Tool for https://api.atlassian.com/flags/api/v2/configurations
@mcp.tool()
async def get_atlassian_feature_configurations(
    atlassian_account_id: str = "712020:8d77ca7f-09f0-4b38-92cf-94b7270b5a34",
    namespace: str = "trello_web",
    api_key: str = "1f24403e-f053-43de-b063-e20b357a8f63"
):
    """
    Retrieves feature flag and configuration settings from Atlassian's flags API.
    
    This tool is used to fetch the state of various feature gates, experiments, and 
    product configurations for a specific user context (identified by Atlassian Account ID) 
    within a specific application namespace (like trello_web).

    Args:
        atlassian_account_id: The unique identifier for the Atlassian user account.
        namespace: The product or application namespace to query.
        api_key: The API key required for authentication with the flags service.
    """
    url = "https://api.atlassian.com/flags/api/v2/configurations"
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "application/json",
        "x-api-key": api_key,
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "namespace": namespace,
        "identifiers": {
            "atlassianAccountId": atlassian_account_id
        },
        "metadata": {
            "isDesktop": False,
            "isTouch": False,
            "locale": "en-US",
            "clientVersion": "build-231871",
            "emailDomain": "gmail.com",
            "hasBC": True,
            "hasMultipleEmails": False,
            "head": "build",
            "idEnterprises": [],
            "idOrgs": ["697e27754fb70f3abb91d906", "697e2779db465a44167ec693"],
            "isClaimable": False,
            "inEnterprise": False,
            "orgs": ["[Redacted]"],
            "signupDate": 1769875257000,
            "premiumFeatures": [
                "activity", "additionalBoardBackgrounds", "additionalStickers", "advancedChecklists",
                "aiQuickCapture", "atlassianIntelligence", "boardExport", "butlerBC", "butlerPremium",
                "collapsibleLists", "csvExport", "customBoardBackgrounds", "customEmoji", "customStickers",
                "deactivated", "export", "goldMembers", "inviteBoard", "inviteOrg", "isBc", "isPremium",
                "largeAttachments", "listColors", "multiBoardGuests", "observers", "paidCorePlugins",
                "plugins", "premiumMirrorCards", "privateTemplates", "readSecrets", "removal",
                "restrictVis", "savedSearches", "shortExportHistory", "starCounts", "superAdmins",
                "tags", "views", "workspaceViews"
            ],
            "products": [110],
            "version": 231871
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"Error: API returned status {e.response.status_code}. Response: {e.response.text}"
        except httpx.RequestError as e:
            return f"Error: A network error occurred while requesting {e.request.url!r}: {str(e)}"
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/gateway/api/tap-delivery/api/v3/personalization/user/712020:8d77ca7f-09f0-4b38-92cf-94b7270b5a34
@mcp.tool()
async def get_trello_user_personalization(user_id: str) -> dict:
    """
    Fetches personalization settings and experimental feature flags for a specific Trello user.

    This tool calls Trello's personalization API to retrieve data related to user-specific 
    UI preferences, feature availability, and tailored content delivery configurations.

    Args:
        user_id (str): The unique identifier for the user (e.g., '712020:8d77ca7f-09f0-4b38-92cf-94b7270b5a34').
    """
    url = f"https://trello.com/gateway/api/tap-delivery/api/v3/personalization/user/{user_id}"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "x-trello-client-version": "build-231871",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "application/json",
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred while fetching personalization data: {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {
                "error": f"An unexpected error occurred: {str(e)}"
            }


# Tool for https://trello.com/1/board/697e3746ad617b8629cef437?fields=id&boardPlugins=true&plugins=enabled
@mcp.tool()
async def get_trello_board_plugins(board_id: str, api_key: str, api_token: str) -> dict:
    """
    Retrieves information about enabled plugins and Power-Ups for a specific Trello board.

    This tool fetches the board's plugin context, including which plugins are currently 
    enabled and their associated metadata.

    Args:
        board_id: The unique identifier for the Trello board.
        api_key: Trello API key for authentication.
        api_token: Trello API token for authentication.
    """
    url = f"https://trello.com/1/board/{board_id}"
    params = {
        "fields": "id",
        "boardPlugins": "true",
        "plugins": "enabled",
        "key": api_key,
        "token": api_token
    }
    headers = {
        "x-trello-operation-name": "BoardPluginsContext",
        "x-trello-operation-source": "graphql",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": "HTTP error occurred",
                "status_code": e.response.status_code,
                "message": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "Network error occurred",
                "message": str(e)
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "message": str(e)
            }


# Tool for https://trello.com/gateway/api/gasv3/api/v1/metadata?product=trello&userId=712020%3A8d77ca7f-09f0-4b38-92cf-94b7270b5a34&userIdType=atlassianAccount&tenantId=&tenantIdType=none
@mcp.tool()
async def get_trello_gateway_metadata(
    user_id: str = "712020:8d77ca7f-09f0-4b38-92cf-94b7270b5a34",
    product: str = "trello",
    user_id_type: str = "atlassianAccount",
    tenant_id: str = "",
    tenant_id_type: str = "none"
) -> dict | str:
    """
    Retrieves metadata for a Trello user session via the Atlassian GASv3 (Global Analytics Service) API.

    This tool queries the Trello gateway to fetch internal metadata associated with a specific user 
    identifier and product context. It is typically used to verify session state or account-level 
    metadata within the Atlassian ecosystem.

    Args:
        user_id: The unique identifier for the user (e.g., an Atlassian account ID).
        product: The name of the product requesting metadata (defaults to 'trello').
        user_id_type: The type of user identifier provided (defaults to 'atlassianAccount').
        tenant_id: Optional identifier for the tenant/organization context.
        tenant_id_type: The type of tenant identifier provided (defaults to 'none').
    """
    url = "https://trello.com/gateway/api/gasv3/api/v1/metadata"
    params = {
        "product": product,
        "userId": user_id,
        "userIdType": user_id_type,
        "tenantId": tenant_id,
        "tenantIdType": tenant_id_type
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while fetching metadata: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting metadata: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/gateway/api/graphql
@mcp.tool()
async def get_trello_unread_quick_capture_notifications(offset: int = 10):
    """
    Retrieves unread 'Quick Capture' notifications for the authenticated Trello user via GraphQL.
    
    Args:
        offset: The number of notifications to fetch (defaults to 10).
    """
    url = "https://trello.com/gateway/api/graphql"
    headers = {
        "atl-client-version": "build-231871",
        "atl-client-name": "Trello Web",
        "content-type": "application/json",
        "apollographql-client-name": "trello-web",
        "apollographql-client-version": "build-231871",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "accept": "*/*"
    }
    
    query = """
    query TrelloNotificationsGetUnreadQuickCapture($offset: Int = 10) {
      trello {
        me @optIn(to: "TrelloMe") {
          id
          notifications(
            filter: {status: "UNREAD", types: ["QUICK_CAPTURE"]}
            first: $offset
          ) @optIn(to: "TrelloMemberNotifications") {
            edges {
              node {
                ... on TrelloQuickCaptureNotification {
                  ...TrelloQuickCaptureNotificationFields
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
    }

    fragment TrelloQuickCaptureNotificationFields on TrelloQuickCaptureNotification {
      id
      card {
        id
        __typename
      }
      __typename
    }
    """
    
    payload = {
        "operationName": "TrelloNotificationsGetUnreadQuickCapture",
        "variables": {"offset": offset},
        "query": query
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error occurred: {e.response.status_code}", "details": e.response.text}
    except httpx.RequestError as e:
        return {"error": f"An error occurred while requesting: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# Tool for https://trello.com/1/boards/697e3746ad617b8629cef437/markAsViewed
@mcp.tool()
async def mark_trello_board_as_viewed(board_id: str, dsc: str) -> str:
    """
    Marks a Trello board as viewed by the user.

    Args:
        board_id: The unique ID of the Trello board.
        dsc: The Trello security token (dsc) required for state-changing requests.
    """
    url = f"https://trello.com/1/boards/{board_id}/markAsViewed"
    
    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest",
        "accept": "*/*"
    }
    
    data = {
        "dsc": dsc
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.text if response.text else "Successfully marked board as viewed."
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://api.atlassian.com/flags/api/v2/frontend/experimentValues
@mcp.tool()
async def get_trello_experiment_values(
    atlassian_account_id: str = "712020:8d77ca7f-09f0-4b38-92cf-94b7270b5a34",
    analytics_anonymous_id: str = "e6e6a109-d7ef-4ad5-8f64-b4a7f1e93aa5",
    workspace_ids: list = None,
    locale: str = "en-US"
):
    """
    Fetches experiment and feature flag values for Trello frontend features.
    
    This tool calls the Atlassian Flags API to determine which experimental features or 
    feature gates are active for a specific user and workspace context.

    Args:
        atlassian_account_id: The unique Atlassian account identifier.
        analytics_anonymous_id: The anonymous analytics identifier.
        workspace_ids: A list of Trello workspace IDs to evaluate flags against.
        locale: The user's locale string (e.g., 'en-US').
    """
    url = "https://api.atlassian.com/flags/api/v2/frontend/experimentValues"
    
    if workspace_ids is None:
        workspace_ids = ["697e27754fb70f3abb91d906"]

    headers = {
        "x-api-key": "1f24403e-f053-43de-b063-e20b357a8f63",
        "x-client-name": "feature-gate-js-client",
        "x-client-version": "0.0.0-development",
        "referer": "https://trello.com/",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    payload = {
        "identifiers": {
            "atlassianAccountId": atlassian_account_id,
            "analyticsAnonymousId": analytics_anonymous_id
        },
        "customAttributes": {
            "inEnterprise": False,
            "version": 231871,
            "locale": locale,
            "isDesktop": False,
            "isTouch": False,
            "idEnterprises": [],
            "workspaceIds": workspace_ids,
            "signupDate": 1769875257000,
            "channel": "main",
            "isPremium": False,
            "isStandard": False,
            "emailDomain": "gmail.com",
            "userEmailDomain": "gmail.com",
            "isClaimable": False,
            "hasMultipleEmails": False,
            "userCohortPersonalProductivity": "ga",
            "userCohortReferralPilot": "not_set",
            "inRealEnterprise": False,
            "hasEnterpriseDomain": False
        },
        "targetApp": "trello_web"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}


# Tool for https://trello.com/gateway/api/session/heartbeat
@mcp.tool()
async def send_trello_session_heartbeat():
    """
    Sends a heartbeat signal to Trello's session gateway to keep the current session active.

    This tool performs a POST request to Trello's internal heartbeat endpoint. It is used 
    to maintain session persistence and prevent the user session from timing out.

    Returns:
        str: The raw response text from the Trello gateway or an error message.
    """
    url = "https://trello.com/gateway/api/session/heartbeat"
    headers = {
        'sec-ch-ua-platform': '"Windows"',
        'referer': 'https://trello.com/b/a7UxwGZY/testboard',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'content-type': 'application/json',
        'sec-ch-ua-mobile': '?0'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while sending heartbeat: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"A request error occurred while sending heartbeat: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/1/organization/697e27754fb70f3abb91d906?fields=id%2CbillableMemberCount%2Coffering%2CteamType
@mcp.tool()
async def get_trello_organization_details(organization_id: str = "697e27754fb70f3abb91d906") -> dict:
    """
    Retrieves metadata and context information for a specific Trello organization (workspace).
    This includes details such as the billable member count, offering type, and team type.

    Args:
        organization_id: The unique identifier of the Trello organization.
    """
    url = f"https://trello.com/1/organization/{organization_id}"
    params = {
        "fields": "id,billableMemberCount,offering,teamType"
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "x-trello-operation-name": "OrganizationContextData",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "x-trello-operation-source": "graphql",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "x-trello-client-version": "build-231871",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": "HTTP error occurred while fetching organization data",
                "status_code": e.response.status_code,
                "detail": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "A networking error occurred",
                "detail": str(e)
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "detail": str(e)
            }


# Tool for https://trello.com/1/member/697e2739e29b3f3210311776?fields=id%2CidPremOrgsAdmin&organizations=all&organization_fields=id%2CavailableLicenseCount%2CdisplayName%2CidEnterprise%2CmaximumLicenseCount%2Coffering%2CpremiumFeatures
@mcp.tool()
async def get_member_organizations(
    member_id: str,
    api_key: str,
    api_token: str
) -> dict:
    """
    Fetch details about a Trello member's organizations, including license information, 
    premium features, and administrative status.

    Args:
        member_id: The unique ID or username of the Trello member.
        api_key: Trello API key for authentication.
        api_token: Trello API token for authentication.
    """
    url = f"https://trello.com/1/member/{member_id}"
    
    params = {
        "fields": "id,idPremOrgsAdmin",
        "organizations": "all",
        "organization_fields": "id,availableLicenseCount,displayName,idEnterprise,maximumLicenseCount,offering,premiumFeatures",
        "key": api_key,
        "token": api_token
    }
    
    headers = {
        "x-trello-operation-name": "MemberOrganizations",
        "x-trello-operation-source": "graphql",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "An error occurred while requesting the Trello API",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "details": str(e)
            }


# Tool for https://trello.com/gateway/api/gasv3/api/v1/metadata?product=trello&userId=712020%3A8d77ca7f-09f0-4b38-92cf-94b7270b5a34&userIdType=atlassianAccount&tenantId=697e27754fb70f3abb91d906&tenantIdType=trelloWorkspaceId
@mcp.tool()
async def get_trello_metadata(
    user_id: str = "712020:8d77ca7f-09f0-4b38-92cf-94b7270b5a34",
    tenant_id: str = "697e27754fb70f3abb91d906",
    product: str = "trello",
    user_id_type: str = "atlassianAccount",
    tenant_id_type: str = "trelloWorkspaceId"
) -> dict:
    """
    Retrieves metadata for a Trello user and workspace from the Atlassian GAS (Global Analytics Service) API.
    
    This tool fetches configuration or context-specific metadata used by the Trello web interface, 
    identifying the user via Atlassian account ID and the workspace via Trello workspace ID.

    Args:
        user_id: The unique identifier for the user (Atlassian Account ID).
        tenant_id: The unique identifier for the Trello workspace (tenant).
        product: The product identifier, defaults to 'trello'.
        user_id_type: The type of user ID provided, defaults to 'atlassianAccount'.
        tenant_id_type: The type of tenant ID provided, defaults to 'trelloWorkspaceId'.
    """
    url = "https://trello.com/gateway/api/gasv3/api/v1/metadata"
    
    params = {
        "product": product,
        "userId": user_id,
        "userIdType": user_id_type,
        "tenantId": tenant_id,
        "tenantIdType": tenant_id_type
    }
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "message": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "A network error occurred",
                "message": str(e)
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "message": str(e)
            }


# Tool for https://trello.com/1/members/me/notificationsCount?grouped=true&filter=all
@mcp.tool()
async def get_trello_notifications_count(api_key: str, api_token: str, grouped: bool = True, filter: str = "all") -> dict:
    """
    Retrieves the count of notifications for the authenticated Trello user.

    This tool calls the Trello API to fetch notification counts, which can be used to 
    determine if there are unread alerts or updates for the user.

    Args:
        api_key: The Trello API key for authentication.
        api_token: The Trello API token for authentication.
        grouped: Whether to return grouped notification counts (default is True).
        filter: The filter to apply to notifications, such as 'all' or 'unread' (default is 'all').

    Returns:
        A dictionary containing the notification count data or an error description.
    """
    url = "https://trello.com/1/members/me/notificationsCount"
    params = {
        "key": api_key,
        "token": api_token,
        "grouped": str(grouped).lower(),
        "filter": filter
    }
    headers = {
        "x-trello-operation-name": "NotificationsCount",
        "accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": "HTTP status error",
                "status_code": e.response.status_code,
                "detail": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "Network request error",
                "detail": str(e)
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "detail": str(e)
            }


# Tool for https://trello.com/1/members/me/notificationGroups?limit=10&skip=0&read_filter=unread&card_fields=id%2Cbadges%2CcardRole%2CcheckItemStates%2Cclosed%2Ccover%2CdateLastActivity%2Cdesc%2CdescData%2Cdue%2CdueComplete%2CdueReminder%2Cemail%2CidAttachmentCover%2CidBoard%2CidChecklists%2CidLabels%2CidList%2CidMembers%2CidMembersVoted%2CidShort%2CisTemplate%2CmanualCoverAttachment%2Cname%2Cpos%2CshortLink%2CshortUrl%2Cstart%2Csubscribed%2Curl&card_board_fields=id%2Cname%2Cprefs%2Csubscribed%2Curl
@mcp.tool()
async def get_unread_notification_groups(
    limit: int = 10,
    skip: int = 0,
    read_filter: str = "unread",
    key: str = None,
    token: str = None
) -> dict:
    """
    Retrieves notification groups for the current member, typically used to show unread activity.
    This includes detailed card and board fields to provide context for the notifications.

    Args:
        limit: The number of notification groups to return (default: 10).
        skip: The number of notification groups to skip for pagination (default: 0).
        read_filter: Filter notifications by status (e.g., 'unread', 'all').
        key: Trello API key.
        token: Trello API token.
    """
    url = "https://trello.com/1/members/me/notificationGroups"
    
    # Extracting the exact fields from the recorded request
    card_fields = "id,badges,cardRole,checkItemStates,closed,cover,dateLastActivity,desc,descData,due,dueComplete,dueReminder,email,idAttachmentCover,idBoard,idChecklists,idLabels,idList,idMembers,idMembersVoted,idShort,isTemplate,manualCoverAttachment,name,pos,shortLink,shortUrl,start,subscribed,url"
    card_board_fields = "id,name,prefs,subscribed,url"
    
    params = {
        "limit": limit,
        "skip": skip,
        "read_filter": read_filter,
        "card_fields": card_fields,
        "card_board_fields": card_board_fields
    }
    
    if key:
        params["key"] = key
    if token:
        params["token"] = token

    headers = {
        "x-trello-operation-name": "UnreadNotificationGroups",
        "x-trello-operation-source": "graphql",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "detail": e.response.text
            }
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://trello.com/1/organization/697e27754fb70f3abb91d906?fields=id%2Cdesc%2CdisplayName%2CidEnterprise%2CidEntitlement%2Cmemberships%2Cname%2Coffering%2Cprefs%2CpremiumFeatures%2Cwebsite&enterprise=true&members=all&member_fields=id%2CfullName%2CmemberType%2CnonPublic&paidAccount=true&paidAccount_fields=standing
@mcp.tool()
async def get_trello_organization_details(organization_id: str) -> dict:
    """
    Retrieve comprehensive details about a Trello organization (workspace), including memberships,
    enterprise status, and paid account standing.

    Args:
        organization_id: The unique ID or name of the Trello organization/workspace.
    """
    url = f"https://trello.com/1/organization/{organization_id}"
    params = {
        "fields": "id,desc,displayName,idEnterprise,idEntitlement,memberships,name,offering,prefs,premiumFeatures,website",
        "enterprise": "true",
        "members": "all",
        "member_fields": "id,fullName,memberType,nonPublic",
        "paidAccount": "true",
        "paidAccount_fields": "standing"
    }
    headers = {
        "x-trello-operation-name": "WorkspacePage",
        "x-trello-operation-source": "graphql",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://trello.com/1/member/697e2739e29b3f3210311776?fields=id%2Cconfirmed%2CidEnterprisesAdmin&enterprises=true&enterprise_filter=saml%2Cmember%2Cmember-unconfirmed&enterprise_fields=id%2Csandbox
@mcp.tool()
async def get_member_enterprise_info(member_id: str) -> dict:
    """
    Retrieves enterprise-related information for a specific Trello member.
    
    This tool fetches details about a member's enterprise associations, including their 
    confirmation status, enterprise administrative rights, and specific enterprise 
    metadata like sandbox status and SAML configuration.

    Args:
        member_id (str): The Trello member ID or username to query.
    """
    url = f"https://trello.com/1/member/{member_id}"
    params = {
        "fields": "id,confirmed,idEnterprisesAdmin",
        "enterprises": "true",
        "enterprise_filter": "saml,member,member-unconfirmed",
        "enterprise_fields": "id,sandbox"
    }
    headers = {
        "x-trello-operation-name": "MemberEnterprisesWithAdmin",
        "x-trello-operation-source": "graphql",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "referer": "https://trello.com/b/a7UxwGZY/testboard"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "message": e.response.text
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "message": str(e)
            }


# Tool for https://trello.com/1/board/697e3746ad617b8629cef437?fields=id&accessRequests=true
@mcp.tool()
async def get_board_access_requests(board_id: str):
    """
    Retrieves the access requests for a specific Trello board.

    This tool queries the Trello API to fetch board information specifically filtered 
     to include pending access requests.

    Args:
        board_id (str): The unique identifier (ID) of the Trello board.
    """
    url = f"https://trello.com/1/board/{board_id}"
    params = {
        "fields": "id",
        "accessRequests": "true"
    }
    headers = {
        "x-trello-operation-name": "BoardAccessRequests",
        "x-trello-operation-source": "graphql",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while fetching access requests: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting access requests: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://api.atlassian.com/flags/api/v2/frontend/experimentValues
@mcp.tool()
async def get_atlassian_experiment_values(
    trello_workspace_id: str,
    atlassian_account_id: str,
    analytics_anonymous_id: str = "e6e6a109-d7ef-4ad5-8f64-b4a7f1e93aa5",
    target_app: str = "trello_web",
    custom_attributes: dict = None
):
    """
    Retrieves frontend experiment and feature flag values from the Atlassian Flags API.
    This tool is used to determine which features or experiments are active for a specific Trello workspace or user context.

    Args:
        trello_workspace_id: The unique identifier for the Trello workspace.
        atlassian_account_id: The Atlassian account ID for the user.
        analytics_anonymous_id: Anonymous ID used for tracking and flag consistency.
        target_app: The application identifier (defaults to 'trello_web').
        custom_attributes: A dictionary of additional context for flag evaluation (e.g., locale, workspaceIds, premium status).
    """
    url = "https://api.atlassian.com/flags/api/v2/frontend/experimentValues"
    
    headers = {
        "x-api-key": "1f24403e-f053-43de-b063-e20b357a8f63",
        "x-client-name": "feature-gate-js-client",
        "x-client-version": "0.0.0-development",
        "content-type": "application/json",
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    # Default attributes if none provided, based on common Trello web patterns
    if custom_attributes is None:
        custom_attributes = {
            "inEnterprise": False,
            "locale": "en-US",
            "workspaceId": trello_workspace_id,
            "workspaceIds": [trello_workspace_id],
            "channel": "main",
            "isPremium": True,
            "isStandard": False
        }

    payload = {
        "identifiers": {
            "trelloWorkspaceId": trello_workspace_id,
            "atlassianAccountId": atlassian_account_id,
            "analyticsAnonymousId": analytics_anonymous_id
        },
        "customAttributes": custom_attributes,
        "targetApp": target_app
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}", "details": e.response.text}
    except httpx.RequestError as e:
        return {"error": "Network request failed", "details": str(e)}
    except Exception as e:
        return {"error": "An unexpected error occurred", "details": str(e)}


# Tool for https://trello-backgrounds.s3.amazonaws.com/SharedBackground/2560x1707/013a0dfc5c37055fbda28f23cc78a554/photo-1742156345582-b857d994c84e.webp
@mcp.tool()
async def fetch_trello_shared_background():
    """
    Fetches a specific high-resolution shared background image from Trello's S3 storage.
    
    This tool retrieves the WebP image resource located at the Trello backgrounds S3 bucket,
    mimicking the browser headers used in the original request.
    """
    url = "https://trello-backgrounds.s3.amazonaws.com/SharedBackground/2560x1707/013a0dfc5c37055fbda28f23cc78a554/photo-1742156345582-b857d994c84e.webp"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Since the response is a binary WebP image, we return a JSON representation 
            # of the result and metadata as per the requirement for text/JSON.
            return {
                "status": "success",
                "url": url,
                "content_type": response.headers.get("Content-Type", "image/webp"),
                "content_length_bytes": len(response.content),
                "message": "Image successfully retrieved."
            }
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error_code": e.response.status_code,
                "message": f"HTTP error occurred while fetching the background: {str(e)}",
                "response_body": e.response.text[:200]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }


# Tool for https://atlassian-cookies--categories.us-east-1.prod.public.atl-paas.net/categories_COOKIE.json
@mcp.tool()
async def get_atlassian_cookie_categories() -> dict:
    """
    Retrieves the classification categories for cookies used by Atlassian services.

    This tool fetches a JSON document containing definitions and metadata for various 
    cookie categories (such as essential, functional, or performance cookies) utilized 
    by Atlassian products like Trello.

    Returns:
        dict: The parsed JSON content containing cookie categories or an error message.
    """
    url = "https://atlassian-cookies--categories.us-east-1.prod.public.atl-paas.net/categories_COOKIE.json"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=20.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            return {"error": f"HTTP error {exc.response.status_code} occurred while fetching categories"}
        except Exception as exc:
            return {"error": f"An unexpected error occurred: {str(exc)}"}


# Tool for https://trello.com/gateway/api/gasv3/api/v1/metadata?product=atlassianCookies&userId=&userIdType=&tenantId=&tenantIdType=
@mcp.tool()
async def get_trello_metadata(
    product: str = "atlassianCookies",
    user_id: str = "",
    user_id_type: str = "",
    tenant_id: str = "",
    tenant_id_type: str = ""
) -> str:
    """
    Fetches Atlassian metadata for the Trello gateway. This tool is typically used to retrieve 
    information related to cookies, user identification, and tenant context within the Atlassian ecosystem.

    Args:
        product: The product identifier, defaults to 'atlassianCookies'.
        user_id: The unique identifier for the user.
        user_id_type: The type category of the user ID.
        tenant_id: The identifier for the tenant/organization.
        tenant_id_type: The type category of the tenant ID.
    """
    url = "https://trello.com/gateway/api/gasv3/api/v1/metadata"
    params = {
        "product": product,
        "userId": user_id,
        "userIdType": user_id_type,
        "tenantId": tenant_id,
        "tenantIdType": tenant_id_type
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while fetching metadata: {str(e)}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting metadata: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/1/boards/697e3746ad617b8629cef437/plugins?filter=enabled&operationName=load:Plugin
@mcp.tool()
async def get_trello_board_plugins(board_id: str) -> any:
    """
    Fetches the list of enabled plugins (Power-Ups) for a specific Trello board.

    This tool interacts with the Trello API to retrieve information about which 
    plugins are currently active on a given board ID. It includes metadata 
    related to the 'load:Plugin' operation.

    Args:
        board_id (str): The unique identifier of the Trello board (e.g., '697e3746ad617b8629cef437').
    """
    url = f"https://trello.com/1/boards/{board_id}/plugins"
    params = {
        "filter": "enabled",
        "operationName": "load:Plugin"
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "x-trello-operation-name": "load:Plugin",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "x-trello-operation-source": "model-loader",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "x-trello-client-version": "build-231871",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "accept": "application/json,text/plain"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code}", "detail": e.response.text}
        except httpx.RequestError as e:
            return {"error": f"An error occurred while requesting your data: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def post_atlassian_batch_analytics(
    batch: list, 
    metadata: dict, 
    sent_at: str
) -> dict | str:
    """
    Sends a batch of telemetry and tracking events to the Atlassian analytics service.

    This tool logs operational data, performance metrics (like TTI and FMP), and user interaction 
    events from applications like Trello. It mimics the batch reporting mechanism used for 
    observability and product analytics.

    Args:
        batch (list): A list of event objects. Each event should include 'context', 'type', 
                      'timestamp', 'userId' or 'anonymousId', and 'properties'.
        metadata (dict): Metadata describing the batch, including 'eventCount', 'signature', 
                         and 'resilienceMechanism'.
        sent_at (str): ISO 8601 timestamp representing when the batch was dispatched.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0",
    }

    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            import json
            response = await client.post(
                url, 
                headers=headers, 
                content=json.dumps(payload)
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
                
    except httpx.HTTPStatusError as e:
        return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def post_atlassian_analytics_batch(batch: list, metadata: dict, sent_at: str = "2026-02-01T06:34:17.511Z") -> dict:
    """
    Sends a batch of telemetry and analytics tracking events to Atlassian's data collection service.

    This tool allows reporting multiple user interactions, operational metrics, and session lifecycle events 
    originating from Atlassian products like Trello. It mimics the behavior of the analytics.js library 
    syncing event buffers to the server.

    Args:
        batch (list): A list of event dictionaries. Each event should contain 'context', 'type', 
                      'timestamp', and 'properties' (detailing the action, actionSubject, etc.).
        metadata (dict): Metadata describing the batch, including 'eventCount', 'signature' for 
                        authentication, and 'metadataClientMetrics'.
        sent_at (str): ISO 8601 timestamp indicating when the batch was transmitted.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "content-type": "text/plain",
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=20.0
            )
            
            # Raise exception for 4xx/5xx responses
            response.raise_for_status()
            
            # Telemetry endpoints often return 204 No Content or simple JSON
            if response.status_code == 204:
                return {"status": "success", "message": "Batch processed successfully"}
            
            try:
                return response.json()
            except Exception:
                return {"status": "success", "response_text": response.text}

    except httpx.HTTPStatusError as e:
        return {
            "error": "HTTP request failed",
            "status_code": e.response.status_code,
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "An unexpected error occurred",
            "message": str(e)
        }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def send_atlassian_analytics_batch(
    batch: list,
    sent_at: str,
    metadata: dict
) -> dict:
    """
    Sends a batch of analytics tracking events to Atlassian's analytics service (v1/batch).
    This endpoint is used by Trello and other Atlassian products to report operational 
    metrics, UI events (like 'taskStart' or 'quickload succeeded'), and user interactions.

    Args:
        batch: A list of event dictionaries. Each event should contain context (locale, screen, 
               library), timestamp, type (e.g., 'track'), userId, anonymousId, properties 
               (environment, product, action, etc.), and a messageId.
        sent_at: The ISO 8601 timestamp indicating when the batch was transmitted.
        metadata: A dictionary containing resilience information and security signatures 
                  required for authentication (e.g., signature, authenticatedUserId).
    """
    url = "https://as.atlassian.com/api/v1/batch"
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    async with httpx.AsyncClient() as client:
        try:
            # We use json=payload to handle the dictionary serialization.
            # While the original request specified text/plain, Atlassian's analytics 
            # collector accepts JSON payloads.
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            
            # Analytics endpoints often return 204 No Content or simple status JSON
            if response.status_code == 204:
                return {"status": "success", "message": "Batch processed successfully"}
                
            try:
                return response.json()
            except Exception:
                return {"status": "success", "response_text": response.text}

        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "Request failed",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "details": str(e)
            }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def send_atlassian_analytics_batch(batch: list, metadata: dict, sent_at: str) -> dict | str:
    """
    Sends a batch of analytics tracking events to the Atlassian analytics service.

    This tool transmits multiple telemetry events (e.g., UI interactions, operational tasks, 
    and performance metrics) collected from Atlassian platforms like Trello to the 
    centralized analytics endpoint.

    Args:
        batch (list): A list of event objects. Each event contains context (locale, screen, 
            library info), timestamps, event types (track), userId, and specific 
            properties/attributes related to the user action.
        metadata (dict): Metadata describing the batch, including event count, resilience 
            mechanisms, and authentication signatures.
        sent_at (str): The ISO 8601 formatted timestamp indicating when the batch 
            request was initiated.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }
    
    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    async with httpx.AsyncClient() as client:
        try:
            # Using json= automatically serializes the dict.
            # Even though the header is text/plain, the payload itself is a JSON string.
            response = await client.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return response.text
                
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting {e.request.url!r}: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://views.unsplash.com/v?app_id=7066&filepath=%2Fphoto-1742156345582-b857d994c84e
@mcp.tool()
async def track_unsplash_photo_view(filepath: str, app_id: str = "7066") -> str:
    """
    Tracks a view event for a specific Unsplash photo via the Unsplash views API.
    
    This function sends a GET request to log that a specific photo has been viewed, 
    typically used for analytics and attribution when Unsplash images are embedded 
    in third-party applications.

    Args:
        filepath (str): The path or identifier of the Unsplash photo (e.g., '/photo-1742156345582-b857d994c84e').
        app_id (str): The application identifier. Defaults to '7066'.
    """
    url = "https://views.unsplash.com/v"
    params = {
        "app_id": app_id,
        "filepath": filepath
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.text if response.text else "View tracked successfully."
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred while tracking view: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def track_atlassian_analytics_batch(batch: list, metadata: dict = None) -> dict:
    """
    Sends a batch of analytics and telemetry events to Atlassian's analytics service.
    This tool is used to report user interactions, performance metrics (like Web Vitals), 
    and feature exposure data for Atlassian products (e.g., Trello).

    Args:
        batch: A list of event objects. Each object should include fields like 'context', 
               'timestamp', 'type', 'userId', 'properties', and 'event'.
        metadata: Optional dictionary containing event metadata such as 'signature', 
                  'authenticatedUserId', and 'eventCount'.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }

    # Prepare the payload following the recorded structure
    payload = {
        "batch": batch,
        "sentAt": "2026-02-01T06:34:17.887Z",  # In a real scenario, this would be generated dynamically
        "metadata": metadata or {
            "eventCount": len(batch),
            "resilienceMechanism": "indexeddb",
            "isUsingFallbackUrl": False,
            "props": {
                "signature": "9cb926c9fb886628dc62b4dbb650293e6442394dc81339b3b55828fbfa192402"
            }
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            # The API specifically uses text/plain even though the content is JSON
            response = await client.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return {"status": "success", "text": response.text}
                
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code} error",
                "details": e.response.text
            }
        except Exception as e:
            return {
                "error": "Unexpected error during request",
                "details": str(e)
            }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def send_atlassian_analytics_batch(batch: list, metadata: dict, sent_at: str) -> dict:
    """
    Sends a batch of analytics tracking events to the Atlassian analytics service.

    This tool is used to report multiple telemetry events in a single request, which is efficient for 
    tracking user interactions, operational status, and performance metrics (like Web Vitals) 
    within Atlassian applications such as Trello.

    Args:
        batch: A list of event objects. Each object typically contains 'context' (browser and environment info), 
               'timestamp', 'type' (e.g., 'track'), 'userId', 'event' name, and 'properties' containing 
               the event details and feature flags.
        metadata: A dictionary containing authentication signatures (e.g., 'authenticatedUserId', 'signature') 
                  and resilience mechanism details used by the analytics client.
        sent_at: The ISO 8601 timestamp indicating when the batch was dispatched to the server.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    
    # Headers based on the recorded request. Note that analytics beacons often use 
    # text/plain to avoid CORS preflight (OPTIONS) requests.
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }
    
    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    async with httpx.AsyncClient() as client:
        try:
            # We use the json parameter for convenience. 
            # Note: In some environments, if the server strictly requires text/plain header 
            # but valid JSON body, one would manually serialize the dict to a string.
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            
            # Returns the JSON response if available, otherwise the raw text
            try:
                return response.json()
            except Exception:
                return {"status": "success", "response_text": response.text}
                
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error {e.response.status_code}",
                "message": e.response.text,
                "url": str(e.request.url)
            }
        except httpx.RequestError as e:
            return {
                "error": "Network error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "error": "Unexpected error",
                "message": str(e)
            }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def submit_atlassian_batch_analytics(batch: list, metadata: dict) -> dict:
    """
    Submits a batch of telemetry and tracking events to Atlassian's analytics service.
    This endpoint is used to aggregate UI interaction data, performance metrics (Web Vitals),
    and operational task successes from products like Trello.

    Args:
        batch (list): A list of tracking event objects. Each event typically includes a context,
                      timestamp, type (e.g., 'track' or 'page'), userId, and specific properties.
        metadata (dict): Metadata associated with the batch request, containing authentication
                         signatures and client metrics.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }

    # The payload structure is reconstructed based on the recorded batch request
    payload = {
        "batch": batch,
        "sentAt": "2026-02-01T06:34:17.981Z",
        "metadata": metadata
    }

    try:
        async with httpx.AsyncClient() as client:
            # Note: While content-type is set to text/plain to match the recording,
            # we send the payload as a JSON object which httpx handles.
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "response_text": response.text
                }

    except httpx.HTTPStatusError as e:
        return {
            "error": "HTTP failure",
            "status_code": e.response.status_code,
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Request failed",
            "message": str(e)
        }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def send_atlassian_batch_analytics(batch: list, metadata: dict = None) -> dict:
    """
    Sends a batch of analytics and tracking events to the Atlassian analytics service.
    This tool allows for reporting multiple events simultaneously, such as user interactions,
    web vitals evaluation, performance measurements, and screen views (e.g., within Trello).

    Args:
        batch (list): A list of event objects. Each event typically contains 'context', 
                      'timestamp', 'type', 'userId', 'properties', and 'event' name.
        metadata (dict, optional): Metadata associated with the batch request, including 
                                   resilience mechanisms and authentication signatures.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0",
    }

    # Construct the payload based on the observed structure
    import json
    payload = {
        "batch": batch,
        "metadata": metadata or {
            "resilienceMechanism": "indexeddb",
            "isUsingFallbackUrl": False
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            # Note: Using content=json.dumps because the service specifically requests 'text/plain' 
            # while receiving JSON data, which is common in analytics ingestion endpoints.
            response = await client.post(
                url, 
                content=json.dumps(payload), 
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": "success", "text": response.text}
                
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "response": e.response.text
            }
        except Exception as e:
            return {"error": f"An error occurred while sending analytics: {str(e)}"}


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def track_atlassian_analytics_batch(batch: list, metadata: dict, sent_at: str = "2026-02-01T06:34:18.609Z") -> dict:
    """
    Sends a batch of analytics and telemetry events to Atlassian's tracking service.
    
    This tool allows for recording user interactions, UI events, and session data 
    associated with Atlassian products like Trello. It dispatches a collection of 
    events in a single batch for efficiency.

    Args:
        batch (list): A list of event dictionaries, each containing 'context', 'type', 'userId', 'properties', etc.
        metadata (dict): Metadata including authentication signatures ('signature', 'authenticatedUserId') and client metrics.
        sent_at (str): The ISO 8601 timestamp representing when the batch was sent.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }
    
    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # We use the json parameter to send the payload; 
            # Note: while the recorded content-type was text/plain, 
            # sending as JSON is standard for this payload structure.
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "response_text": response.text
                }
                
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "message": str(e),
                "details": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "A request error occurred while connecting to the analytics service",
                "message": str(e)
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "details": str(e)
            }


# Tool for https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/app-switcher-fe_manifest_v1.json
@mcp.tool()
async def get_app_switcher_manifest():
    """
    Fetches the app-switcher frontend manifest from the Atlassian frontend configuration service.
    
    This manifest contains the versioning, asset paths, and configuration for the 
    application switcher used in Trello and other Atlassian products.

    Returns:
        dict: The parsed JSON manifest data if successful.
        str: An error message if the request fails.
    """
    url = "https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/app-switcher-fe_manifest_v1.json"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"An error occurred while requesting the manifest: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# Tool for https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/v002-n_app-switcher-fe-e_prod-west-l_en-US-v_do-not-parse-1769732089832-f_commercial.json
@mcp.tool()
async def fetch_atlassian_app_switcher_config() -> dict:
    """
    Fetches the Atlassian App Switcher configuration JSON from the Bifrost frontend configuration service.

    This tool retrieves the production configuration for the 'app-switcher-fe' component, 
    specifically for the US English locale and commercial environments. This configuration 
    is typically used by Atlassian products like Trello to define navigation and switcher options.

    Returns:
        dict: The parsed configuration data if successful, or an error description.
    """
    url = "https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/v002-n_app-switcher-fe-e_prod-west-l_en-US-v_do-not-parse-1769732089832-f_commercial.json"
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "detail": "Failed to retrieve the Bifrost configuration asset."
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred",
                "detail": str(e)
            }


# Tool for https://trello.com/gateway/api/app-switcher/api/app-switcher/v1/third-party-products?source=app-switcher-fe&product=trello
@mcp.tool()
async def get_trello_third_party_products() -> str:
    """
    Fetches the list of third-party products available in the Trello app switcher.
    
    This tool calls the internal Atlassian gateway API used by Trello to retrieve 
    metadata regarding integrated third-party products shown in the UI's application switcher.

    Returns:
        The JSON response string containing third-party product definitions or an error message.
    """
    url = "https://trello.com/gateway/api/app-switcher/api/app-switcher/v1/third-party-products"
    params = {
        "source": "app-switcher-fe",
        "product": "trello"
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "atl-app-switcher-private-api": "true",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "atl-app-switcher-version": "45.0.5",
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting {e.request.url!r}: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/gateway/api/app-switcher/api/available-products?source=app-switcher-fe&product=trello
@mcp.tool()
async def get_available_trello_products():
    """
    Retrieves a list of available Atlassian products and services accessible from the Trello app switcher.
    
    This tool calls the Trello/Atlassian gateway API to determine which related products 
    (such as Jira or Confluence) are available for the current user session.

    Returns:
        The JSON response containing available products or an error message if the request fails.
    """
    url = "https://trello.com/gateway/api/app-switcher/api/available-products"
    params = {
        "source": "app-switcher-fe",
        "product": "trello"
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "atl-app-switcher-private-api": "true",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "atl-app-switcher-version": "45.0.5",
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/gateway/api/app-switcher/api/app-switcher/v1/third-party-products?source=app-switcher-fe&product=trello
@mcp.tool()
async def get_trello_app_switcher_third_party_products():
    """
    Fetches the list of third-party products available in the Trello app switcher.

    This tool communicates with Trello's private gateway API to retrieve information about 
    external products and integrations compatible with the current Trello session.

    Returns:
        dict: The parsed JSON response from the Trello API or an error object.
    """
    url = "https://trello.com/gateway/api/app-switcher/api/app-switcher/v1/third-party-products"
    params = {
        "source": "app-switcher-fe",
        "product": "trello"
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "atl-app-switcher-private-api": "true",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "atl-app-switcher-version": "45.1.2",
        "sec-ch-ua-mobile": "?0"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": "HTTP request failed",
            "status_code": e.response.status_code,
            "message": e.response.text
        }
    except Exception as e:
        return {
            "error": "An unexpected error occurred",
            "details": str(e)
        }


# Tool for https://trello.com/gateway/api/app-switcher/api/available-products?source=app-switcher-fe&product=trello
@mcp.tool()
async def get_available_trello_products(source: str = "app-switcher-fe", product: str = "trello"):
    """
    Fetches the list of available Atlassian products from the Trello app-switcher gateway.

    This tool queries the Trello gateway API used by the application switcher to identify 
    which Atlassian products and services are currently available for the user session.

    Args:
        source: The source application or component making the request (default: "app-switcher-fe").
        product: The product context for the availability check (default: "trello").
    """
    url = "https://trello.com/gateway/api/app-switcher/api/available-products"
    params = {
        "source": source,
        "product": product
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "atl-app-switcher-private-api": "true",
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "atl-app-switcher-version": "45.1.2",
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return response.text
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/app-switcher-fe_manifest_v1.json
@mcp.tool()
async def get_app_switcher_manifest() -> dict | str:
    """
    Fetches the app-switcher frontend manifest from Atlassian's configuration service.
    
    This tool retrieves the manifest file for the 'app-switcher-fe' component, which 
    contains versioning and asset information used by frontend applications like Trello.
    
    Returns:
        dict: The parsed JSON manifest if successful.
        str: An error message if the request fails.
    """
    url = "https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/app-switcher-fe_manifest_v1.json"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting the manifest: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/v002-n_app-switcher-fe-e_prod-west-l_en-US-v_do-not-parse-1769732089832-f_commercial.json
@mcp.tool()
async def get_app_switcher_config():
    """
    Fetches the application switcher configuration asset from the Atlassian Bifrost configuration service.
    
    This tool retrieves the commercial JSON configuration for the app-switcher-fe component,
    which is used by Trello and other Atlassian products to manage frontend navigation and feature flags.

    Returns:
        dict: The parsed JSON configuration if successful, or a string error message.
    """
    url = "https://fd-config-bifrost.prod-east.frontend.public.atl-paas.net/assets/v002-n_app-switcher-fe-e_prod-west-l_en-US-v_do-not-parse-1769732089832-f_commercial.json"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting {e.request.url!r}: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/gateway/api/post-office/api/v1/placements/app-switcher-discovery-section?locale=en-US&product=trello&workspaceAri=no-workspace-ari-available
@mcp.tool()
async def get_app_switcher_discovery(
    locale: str = "en-US",
    product: str = "trello",
    workspace_ari: str = "no-workspace-ari-available"
) -> dict:
    """
    Fetches the app switcher discovery section placements from the Trello gateway API.
    This tool retrieves promotional or functional placements for the Trello UI based on the user's context.

    Args:
        locale (str): The language and region code for the request.
        product (str): The specific product identifier, typically 'trello'.
        workspace_ari (str): The Atlassian Resource Identifier for the workspace, or a fallback string if unavailable.
    """
    url = "https://trello.com/gateway/api/post-office/api/v1/placements/app-switcher-discovery-section"
    params = {
        "locale": locale,
        "product": product,
        "workspaceAri": workspace_ari
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code}", "detail": e.response.text}
        except httpx.RequestError as e:
            return {"error": f"An error occurred while requesting {e.request.url!r}: {str(e)}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def send_atlassian_analytics_batch(batch: list, metadata: dict, sent_at: str) -> dict:
    """
    Sends a batch of tracking and analytics events to Atlassian's analytics service.
    This is used to record UI interactions, performance metrics (web-vitals), and 
    operational task events for Atlassian products like Trello.

    Args:
        batch (list): A list of event objects containing 'context', 'type', 'userId', 'properties', etc.
        metadata (dict): Batch-level metadata including signatures and client metrics.
        sent_at (str): ISO 8601 timestamp indicating when the batch was dispatched.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "content-type": "text/plain",
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "batch": batch,
        "metadata": metadata,
        "sentAt": sent_at
    }

    async with httpx.AsyncClient() as client:
        try:
            # Note: The original request uses text/plain but sends JSON data.
            # Using the 'json' parameter in httpx defaults to application/json.
            # If the server strictly requires text/plain, we would use 'content'.
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return {"status": "success", "text": response.text}
                
        except httpx.HTTPStatusError as e:
            return {
                "error": "HTTP Error",
                "status_code": e.response.status_code,
                "message": str(e),
                "response": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": "Network Error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "error": "Unexpected Error",
                "message": str(e)
            }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def post_atlassian_batch_analytics(batch: list, metadata: dict, sent_at: str = "2026-02-01T06:34:20.256Z") -> dict:
    """
    Submits a batch of telemetry and analytics events to Atlassian's tracking infrastructure.
    
    This tool is used to record frontend activities, performance metrics (UFO), and UI 
    interactions within Atlassian products like Trello. It supports batching multiple 
    'track' and 'experience measured' event types into a single POST request to the 
    Atlassian analytics service.

    Args:
        batch: A list of event objects containing context (browser/screen info), timing, type, and property data.
        metadata: Client-side metadata including security signatures, resilience mechanisms, and user identification.
        sent_at: The ISO 8601 timestamp indicating when the batch was dispatched.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }
    
    body = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=body,
                headers=headers,
                timeout=15.0
            )
            response.raise_for_status()
            
            # Analytics endpoints often return 204 No Content or empty 200 responses
            if response.status_code == 204 or not response.text:
                return {"status": "success", "code": response.status_code}
            
            try:
                return response.json()
            except Exception:
                return {"status": "success", "response_text": response.text}
                
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Request failed",
            "details": str(e)
        }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def send_atlassian_analytics_batch(batch: list, sent_at: str, metadata: dict) -> dict | str:
    """
    Sends a batch of analytics and tracking events to the Atlassian telemetry service.
    
    This tool allows for the bulk submission of telemetry data, including user tracking,
    performance metrics (experience measurement), and UI interaction events typically
    originating from Trello or other Atlassian web platforms.
    
    Args:
        batch (list): A list of event dictionaries. Each item typically contains context 
                      (locale, screen, userAgent), a timestamp, event type (e.g., 'track'), 
                      and detailed properties/attributes.
        sent_at (str): The ISO 8601 timestamp representing when the batch was dispatched.
        metadata (dict): Metadata containing security signatures and authenticated user information 
                         required to validate the batch.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    async with httpx.AsyncClient() as client:
        try:
            # We manually serialize the JSON and send it as text/plain to match the 
            # original request's behavior, which often bypasses certain CORS preflights.
            import json
            serialized_payload = json.dumps(payload)
            
            response = await client.post(
                url, 
                headers=headers, 
                content=serialized_payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except (ValueError, json.JSONDecodeError):
                return response.text
                
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An error occurred while sending analytics: {str(e)}"


# Tool for https://trello.com/gateway/api/post-office/api/v1/messages/lifecycle/bulk
@mcp.tool()
async def report_trello_lifecycle_bulk(messages: list) -> dict:
    """
    Reports bulk lifecycle events (e.g., 'viewed') for Trello app messages or recommendations.
    
    This tool sends tracking data to Trello's internal "Post Office" API to monitor how 
    users interact with UI elements like the app switcher discovery section. It is 
    primarily used for analytics and maintaining the state of recommendations.

    Args:
        messages (list): A list of dictionaries representing lifecycle events.
                         Each dictionary should contain 'messageInstanceId', 'messageTemplateId',
                         'type', 'placement', 'createdAt', and 'context' (containing browser 
                         and recommendation metadata).
    """
    url = "https://trello.com/gateway/api/post-office/api/v1/messages/lifecycle/bulk"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "application/json",
        "sec-ch-ua-mobile": "?0"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, 
                headers=headers, 
                json=messages,
                timeout=30.0
            )
            response.raise_for_status()
            
            # The API might return an empty 200/204 response on success
            if response.status_code in (200, 201, 204):
                try:
                    return response.json()
                except Exception:
                    return {"status": "success", "status_code": response.status_code}
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://trello.com/gateway/api/post-office/api/v1/message-instance-event/bulk
@mcp.tool()
async def bulk_track_trello_message_events(events: list) -> dict:
    """
    Reports a bulk collection of message instance events to Trello's tracking gateway.
    This tool is used to log telemetry data such as message delivery success, views, 
    and interactions for in-app recommendations and notifications.

    Args:
        events (list): A list of dictionaries representing the events to track. 
                       Each event includes fields like messageEventType, messageInstanceId, 
                       messageTemplateId, placementId, and context metadata.
    """
    url = "https://trello.com/gateway/api/post-office/api/v1/message-instance-event/bulk"
    headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "referer": "https://trello.com/",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"'
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=events, 
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Analytics endpoints often return 204 No Content
            if response.status_code == 204:
                return {"status": "success", "detail": "Events reported successfully"}
            
            try:
                return response.json()
            except Exception:
                return {"status": "success", "response_text": response.text}

    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except httpx.RequestError as e:
        return {"error": f"Network error occurred: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def post_atlassian_analytics_batch(
    batch: list,
    metadata: dict,
    sent_at: str = "2026-02-01T06:34:21.124Z"
) -> dict:
    """
    Sends a batch of telemetry, tracking, and operational events to Atlassian's analytics service.
    This tool is used to log user interactions, performance metrics (like TTI/FMP), and 
    experience statuses for Atlassian products like Trello.

    Args:
        batch: A list of event dictionaries. Each event should include context, timestamp, 
               type (e.g., 'track'), userId, and properties including actionSubject and action.
        metadata: Metadata for the batch, including resilience mechanism details and 
                  security signatures (e.g., authenticatedUserId).
        sent_at: The ISO 8601 timestamp indicating when the batch was dispatched.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    
    # Using the headers observed in the recorded request.
    # Note: content-type is set to 'text/plain' as observed, which is common for 
    # analytics beacons to avoid CORS preflight overhead.
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # We send the JSON payload but with the text/plain header as required by the endpoint
            import json
            response = await client.post(
                url, 
                content=json.dumps(payload), 
                headers=headers
            )
            
            # If the response is 204 No Content (common for analytics), return success
            if response.status_code == 204:
                return {"status": "success", "message": "Batch accepted (No Content)"}
                
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": "success", "response_text": response.text}

    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Failed to send analytics batch",
            "details": str(e)
        }


# Tool for https://trello.com/proxy/unsplash/collections/317099/photos?per_page=30&order_by=latest&page=1
@mcp.tool()
async def get_trello_unsplash_collection_photos(
    collection_id: str = "317099",
    per_page: int = 30,
    order_by: str = "latest",
    page: int = 1
) -> dict | str:
    """
    Fetches a list of photos from a specific Unsplash collection using the Trello proxy.

    Args:
        collection_id: The unique identifier of the Unsplash collection.
        per_page: The number of photos to return per page (max 30).
        order_by: Sort order for the photos (e.g., 'latest', 'oldest', 'popular').
        page: The page number to retrieve.
    """
    url = f"https://trello.com/proxy/unsplash/collections/{collection_id}/photos"
    
    params = {
        "per_page": per_page,
        "order_by": order_by,
        "page": page
    }
    
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/b/a7UxwGZY/testboard",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "accept-version": "v1",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting {e.request.url!r}: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# Tool for https://trello.com/1/organization/697e27754fb70f3abb91d906?fields=id%2Cmemberships%2CpremiumFeatures&memberships=me
@mcp.tool()
async def get_trello_organization_details(organization_id: str = "697e27754fb70f3abb91d906"):
    """
    Retrieves specific details for a Trello organization (workspace), including memberships and premium features.

    This tool queries the Trello API for a specific workspace ID to get its core identification,
    the membership status of the current user, and the premium features enabled for that workspace.

    Args:
        organization_id (str): The unique ID of the Trello organization/workspace.
    """
    url = f"https://trello.com/1/organization/{organization_id}"
    params = {
        "fields": "id,memberships,premiumFeatures",
        "memberships": "me"
    }
    headers = {
        "x-trello-operation-name": "HeaderCreateMenuPopoverWorkspace",
        "x-trello-operation-source": "graphql",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, 
                params=params, 
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"HTTP {exc.response.status_code} error while retrieving organization details",
                "details": exc.response.text
            }
        except Exception as exc:
            return {
                "error": "An unexpected error occurred",
                "message": str(exc)
            }


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def send_atlassian_analytics_batch(
    batch: list,
    sent_at: str,
    metadata: dict
) -> dict | str:
    """
    Sends a batch of analytics, tracking, and operational events to Atlassian's analytics service.

    This tool is used to log user interactions, experience measurements, and system operational
    tasks (e.g., task aborts, menu item views, button clicks) for Atlassian products like Trello.
    It transmits data including user context, session IDs, and feature flag states.

    Args:
        batch (list): A list of event objects. Each object contains context (browser/OS info), 
                      timestamps, event types, user identifiers, and specific event properties.
        sent_at (str): The ISO 8601 timestamp representing when the batch was dispatched.
        metadata (dict): Metadata including event counts, authentication signatures, and client metrics.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "content-type": "text/plain",
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    try:
        async with httpx.AsyncClient() as client:
            # We use the json parameter to handle serialization. 
            # Note: While the original request used text/plain, most Atlassian endpoints 
            # accept application/json or parse text/plain content as JSON.
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return response.text
                
    except httpx.HTTPStatusError as e:
        return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# Tool for https://as.atlassian.com/api/v1/batch
@mcp.tool()
async def post_atlassian_batch_analytics(batch: list, metadata: dict, sent_at: str) -> dict | str:
    """
    Sends a batch of analytics and telemetry events to the Atlassian analytics service.

    This tool is designed to submit multiple tracking events in a single request, which is 
    commonly used by Atlassian products like Trello to log user interactions, UI events, 
    and system performance metrics.

    Args:
        batch (list): A list of analytics event objects. Each object contains context (locale, screen), 
                      event type (e.g., 'track'), userId, and detailed properties of the action.
        metadata (dict): Metadata providing context for the batch, such as event count, resilience 
                         mechanisms, and client-side metrics.
        sent_at (str): The ISO 8601 timestamp indicating when the batch was dispatched from the client.
    """
    url = "https://as.atlassian.com/api/v1/batch"
    headers = {
        "content-type": "text/plain",
        "referer": "https://trello.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Chromium";v="145", "Not:A-Brand";v="99"',
        "sec-ch-ua-mobile": "?0"
    }

    payload = {
        "batch": batch,
        "sentAt": sent_at,
        "metadata": metadata
    }

    async with httpx.AsyncClient() as client:
        try:
            # Note: We use the json parameter which automatically serializes the dict.
            # While the original request used text/plain to avoid CORS preflights in a browser,
            # application/json is the standard for programmatic API access.
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return response.text
                
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
