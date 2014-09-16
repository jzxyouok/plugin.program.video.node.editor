# coding=utf-8
import os, sys, shutil
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import xml.etree.ElementTree as xmltree
from traceback import print_exc

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id').decode( 'utf-8' )
__addonversion__ = __addon__.getAddonInfo('version')
__language__     = __addon__.getLocalizedString
__cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
__defaultpath__  = xbmc.translatePath( os.path.join( __cwd__, 'resources' ).encode("utf-8") ).decode("utf-8")

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)
    
class RuleFunctions():
    def __init__(self):
        self.nodeRules = None

    def _load_rules( self ):
        overridepath = os.path.join( __defaultpath__ , "rules.xml" )
        try:
            tree = xmltree.parse( overridepath )
            return tree
        except:
            return None
            
    def translateRule( self, rule ):
        # Load the rules
        tree = self._load_rules()
        hasValue = True
        
        elems = tree.getroot().find( "matches" ).findall( "match" )
        for elem in elems:
            if elem.attrib.get( "name" ) == rule[ 0 ]:
                match = xbmc.getLocalizedString( int( elem.find( "label" ).text ) )
                group = elem.find( "operator" ).text
                
        elems = tree.getroot().find( "operators" ).findall( "group" )
        operator = None
        defaultOperator = None
        defaultOperatorValue = None
        for elem in elems:
            if elem.attrib.get( "name" ) == group:
                for operators in elem.findall( "operator" ):
                    if operators.text == rule[ 1 ]:
                        operator = xbmc.getLocalizedString( int( operators.attrib.get( "label" ) ) )
                    if defaultOperator is None:
                        defaultOperator = xbmc.getLocalizedString( int( operators.attrib.get( "label" ) ) )
                        defaultOperatorValue = operators.text
                        
                if "option" in elem.attrib:
                    hasValue = False
                    
        # If we didn't match an operator, set it to the default
        if operator is None:
            operator = defaultOperator
            rule[ 1 ] = defaultOperatorValue
                    
        if hasValue == False:
            return [ [ match, rule[ 0 ] ], [ operator, group, rule[ 1 ] ], [ "|NONE|", "<No value>" ] ]
            
        if len( rule ) == 2 or rule[ 2 ] == "" or rule[ 2 ] is None:
            return [ [ match, rule[ 0 ] ], [ operator, group, rule[ 1 ] ], [ "", "<No value>" ] ]
            
        return [ [ match, rule[ 0 ] ], [ operator, group, rule[ 1 ] ], [ rule[ 2 ], rule[ 2 ] ] ]
        
    def displayRule( self, actionPath, path, ruleNum ):
        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            
            # Get the content type
            content = root.find( "content" )
            if content is not None:
                content = content.text
            else:
                content = "NONE"
            
            # Get all the rules
            ruleCount = 0
            rules = root.findall( "rule" )
            if rules is not None:
                for rule in rules:
                    if str( ruleCount ) == ruleNum:
                        value = rule.find( "value" )
                        if value is None:
                            value = ""
                        else:
                            value = value.text
                            
                        translated = self.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), value ] )
                        
                        # Rule to change match
                        listitem = xbmcgui.ListItem( label="%s" % ( translated[ 0 ][ 0 ] ) )
                        action = "plugin://plugin.program.video.node.editor?type=editMatch&actionPath=" + actionPath + "&content=" + content + "&default=" + translated[ 0 ][ 1 ] + "&rule=" + str( ruleCount )
                        xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )

                        listitem = xbmcgui.ListItem( label="%s" % ( translated[ 1 ][ 0 ] ) )
                        action = "plugin://plugin.program.video.node.editor?type=editOperator&actionPath=" + actionPath + "&group=" + translated[ 1 ][ 1 ] + "&default=" + translated[ 1 ][ 2 ] + "&rule=" + str( ruleCount )
                        xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )
                        
                        if not ( translated[ 2 ][ 0 ] ) == "|NONE|":
                            listitem = xbmcgui.ListItem( label="%s" % ( translated[ 2 ][ 1 ] ) )
                            action = "plugin://plugin.program.video.node.editor?type=editValue&actionPath=" + actionPath + "&rule=" + str( ruleCount )
                            
                            # Check if this match type can be browsed
                            if self.canBrowse( translated[ 0 ][ 1 ], content ):
                                listitem.addContextMenuItems( [(__language__(30107), "XBMC.RunPlugin(plugin://plugin.program.video.node.editor?type=browseValue&actionPath=" + actionPath + "&rule=" + str( ruleCount ) + "&match=" + translated[ 0 ][ 1 ] + "&content=" + content + ")" )], replaceItems = True )
                            xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )
                            
                            #self.browse( translated[ 0 ][ 1 ], content )
                        
                        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
                        
                        return

                    ruleCount = ruleCount + 1
        except:
            print_exc()
        
    def editMatch( self, actionPath, ruleNum, content, default ):
        # Load all operator groups
        tree = self._load_rules().getroot()
        elems = tree.find( "matches" ).findall( "match" )
        
        selectName = []
        selectValue = []
        
        # Find the matches for the content we've been passed
        for elem in elems:
            if content != "NONE":
                contentMatch = elem.find( content )
                if contentMatch is not None:
                    selectName.append( xbmc.getLocalizedString( int( elem.find( "label" ).text ) ) )
                    selectValue.append( elem.attrib.get( "name" ) )
                else:
                    pass
            else:
                selectName.append( xbmc.getLocalizedString( int( elem.find( "label" ).text ) ) )
                selectValue.append( elem.attrib.get( "name" ) )
                    
        # Let the user select an operator
        selectedOperator = xbmcgui.Dialog().select( __language__( 30305 ), selectName )
        
        # If the user selected no operator...
        if selectedOperator == -1:
            return
        
        self.writeUpdatedRule( actionPath, ruleNum, match = selectValue[ selectedOperator ] )
        
    def editOperator( self, actionPath, ruleNum, group, default ):
        # Load all operator groups
        tree = self._load_rules().getroot()
        elems = tree.find( "operators" ).findall( "group" )
        
        selectName = []
        selectValue = []
        
        # Find the group we've been passed and load its operators
        for elem in elems:
            if elem.attrib.get( "name" ) == group:
                for operators in elem.findall( "operator" ):
                    selectName.append( xbmc.getLocalizedString( int( operators.attrib.get( "label" ) ) ) )
                    selectValue.append( operators.text )
                    
        # Let the user select an operator
        selectedOperator = xbmcgui.Dialog().select( __language__( 30306 ), selectName )
        
        # If the user selected no operator...
        if selectedOperator == -1:
            return
        
        self.writeUpdatedRule( actionPath, ruleNum, operator = selectValue[ selectedOperator ] )
        
    def editValue( self, actionPath, ruleNum ):
        # This function is the entry point for editing the value of a rule
        # Because we can't always pass the current value through the uri, we first need
        # to retrieve it, and the operator data type
        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            
            # Get all the rules
            ruleCount = 0
            rules = root.findall( "rule" )
            if rules is not None:
                for rule in rules:
                    if str( ruleCount ) == ruleNum:
                        # This is the rule we'll be updating
                        
                        # Get the current value
                        curValue = rule.find( "value" )
                        if curValue is None:
                            curValue = ""
                        else:
                            curValue = curValue.text
                            
                        match = rule.attrib.get( "field" )
                        operator = rule.attrib.get( "operator" )

                    ruleCount = ruleCount + 1
                        
            # Now, use the match value to get the group of operators this
            # comes from (this will tell us the data type in all types
            # but "date")
            tree = self._load_rules().getroot()
            elems = tree.find( "matches" ).findall( "match" )
            for elem in elems:
                if elem.attrib.get( "name" ) == match:
                    group = elem.find( "operator" ).text
                    
            if group == "date":
                # We probably should go through the tree again, but we'll just check
                # for string ending in "inthelast", and switch the type to numeric
                if operator.endswith( "inthelast" ):
                    group = "numeric"
                    
            # Set the type of text entry dialog to be used
            if group == "string":
                type = xbmcgui.INPUT_ALPHANUM
            if group == "numeric":
                type = xbmcgui.INPUT_NUMERIC
            if group == "time":
                type = xbmcgui.INPUT_TIME
            if group == "date":
                type = xbmcgui.INPUT_DATE
            if group == "isornot":
                type = xbmcgui.INPUT_ALPHANUM
                
            returnVal = xbmcgui.Dialog().input( __language__( 30307 ), curValue, type=type )
            if returnVal != "":
                self.writeUpdatedRule( actionPath, ruleNum, value=returnVal.decode( "utf-8" ) )
            
        except:
            print_exc()
            
    def writeUpdatedRule( self, actionPath, ruleNum, match = None, operator = None, value = None ):
        # This function writes an updated match, operator or value to a rule
        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            
            # Get all the rules
            ruleCount = 0
            rules = root.findall( "rule" )
            if rules is not None:
                for rule in rules:
                    if str( ruleCount ) == ruleNum:
                        # This is the rule we're updating
                        valueElem = rule.find( "value" )
                        
                        # Get the original rule
                        if actionPath.endswith( "index.xml" ):
                            origMatch = rule.attrib.get( "field" )
                            origOperator = rule.attrib.get( "operator" )
                            if valueElem is None:
                                origValue = ""
                            else:
                                origValue = valueElem.text
                                
                            originalRule = self.translateRule( [ origMatch, origOperator, origValue ] )
                        
                        # Get the updated rule
                        if match is None:
                            match = rule.attrib.get( "field" )
                        if operator is None:
                            operator = rule.attrib.get( "operator" )
                            
                        if value is None:
                            if valueElem is None:
                                value = ""
                            else:
                                value = valueElem.text
                                
                        if value is None:
                            value = ""
                                
                        translated = self.translateRule( [ match, operator, value ] )
                        
                        # Update the rule
                        rule.set( "field", translated[ 0 ][ 1 ] )
                        rule.set( "operator", translated[ 1 ][ 2 ] )
                        if len( translated ) == 3:
                            if rule.find( "value" ) == None:
                                # Create a new rule node
                                xmltree.SubElement( rule, "value" ).text = translated[ 2 ][ 0 ]
                            else:
                                rule.find( "value" ).text = translated[ 2 ][ 0 ]
                                
                    ruleCount = ruleCount + 1
                        
            # Save the file
            self.indent( root )
            tree.write( actionPath, encoding="UTF-8" )
            
            # Update the other files in the directory
            if actionPath.endswith( "index.xml" ):
                ( filePath, fileName ) = os.path.split( actionPath )
                self.editNodeRule( filePath, originalRule, translated )
        except:
            print_exc()
            
    def newRule( self, actionPath ):
        # This function adds a new rule, with default match and operator, no value
        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            
            # Get the content type
            content = root.find( "content" )
            
            # Find the default match for this content type
            ruleTree = self._load_rules().getroot()
            elems = ruleTree.find( "matches" ).findall( "match" )
            match = "title"
            for elem in elems:
                if content is not None:
                    contentCheck = elem.find( content.text )
                    if contentCheck is not None:
                        # We've found the first match for this type
                        match = elem.attrib.get( "name" )
                        operator = elem.find( "operator" ).text
                        break
                else:
                    # We've found the first match for this type
                    match = elem.attrib.get( "name" )
                    operator = elem.find( "operator" ).text
                    break
                    
            # Find the default operator for this match
            elems = ruleTree.find( "operators" ).findall( "group" )
            for elem in elems:
                if elem.attrib.get( "name" ) == operator:
                    operator = elem.find( "operator" ).text
                    break
                    
            # Write the new rule
            newRule = xmltree.SubElement( root, "rule" )
            newRule.set( "field", match )
            newRule.set( "operator", operator )
            xmltree.SubElement( newRule, "value" )                               
            
            # Save the file
            self.indent( root )
            tree.write( actionPath, encoding="UTF-8" )
            
            if actionPath.endswith( "index.xml" ):
                ( filePath, fileName ) = os.path.split( actionPath )
                newRule = self.translateRule( [ match, operator, "" ] )
                self.addNodeRule( filePath, newRule )
        except:
            print_exc()
            
    def deleteRule( self, actionPath, ruleNum ):
        # This function deletes a rule
        result = xbmcgui.Dialog().yesno(__addonname__, __language__( 30405 ) )
        if not result:
            return
            
        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            
            # Get all the rules
            ruleCount = 0
            rules = root.findall( "rule" )
            if rules is not None:
                for rule in rules:
                    if str( ruleCount ) == ruleNum:
                        # This is the rule we want to delete
                        if actionPath.endswith( "index.xml" ):
                            # Translate the rule, so we can delete it from the views
                            valueElem = rule.find( "value" )
                            origMatch = rule.attrib.get( "field" )
                            origOperator = rule.attrib.get( "operator" )
                            if valueElem is None:
                                origValue = ""
                            else:
                                origValue = valueElem.text
                                
                            originalRule = self.translateRule( [ origMatch, origOperator, origValue ] )
                            
                        # Delete the rule
                        root.remove( rule )
                        break

                    ruleCount = ruleCount + 1
                                
            # Save the file
            self.indent( root )
            tree.write( actionPath, encoding="UTF-8" )
            
            if actionPath.endswith( "index.xml" ):
                ( filePath, fileName ) = os.path.split( actionPath )
                self.deleteNodeRule( filePath, originalRule )
        
        except:
            print_exc()
            
    
    # Functions for managing rules in all views
    def addNodeRule( self, actionPath, newRule ):
        dirs, files = xbmcvfs.listdir( actionPath )
        for file in files:
            if file == "index.xml":
                continue
            elif file.endswith( ".xml" ):
                filename = os.path.join( actionPath, file )
                
                try:
                    # Load the xml file
                    tree = xmltree.parse( filename )
                    root = tree.getroot()
                    
                    rule = xmltree.SubElement( root, "rule" )
                    rule.set( "field", newRule[ 0 ][ 1 ] )
                    rule.set( "operator", newRule[ 1 ][ 0 ] )
                    xmltree.SubElement( rule, "value" ).text = newRule[ 2 ][ 0 ]
                    
                    # Save the file
                    self.indent( root )
                    tree.write( filename, encoding="UTF-8" )
                except:
                    print_exc()

                
                
    def editNodeRule( self, actionPath, originalRule, newRule ):
        dirs, files = xbmcvfs.listdir( actionPath )
        for file in files:
            if file == "index.xml":
                continue
            elif file.endswith( ".xml" ):
                filename = os.path.join( actionPath, file )
                
                # List the rules
                try:
                    # Load the xml file
                    tree = xmltree.parse( filename )
                    root = tree.getroot()
                    
                    # Look for any rules
                    rules = root.findall( "rule" )
                    if rules is not None:
                        for rule in rules:
                            value = rule.find( "value" )
                            if value is not None and value.text is not None:
                                translated = self.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), value.text ] )
                            else:
                                translated = self.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), "" ] )

                            if originalRule[ 0 ][ 1 ] == translated[ 0 ][ 1 ] and originalRule[ 1 ][ 0 ] == translated[ 1 ][ 0 ] and originalRule[ 2 ][ 0 ] == translated[ 2 ][ 0 ]:
                                # This is the right rule, update it
                                rule.set( "field", newRule[ 0 ][ 1 ] )
                                rule.set( "operator", newRule[ 1 ][ 0 ] )
                                if value is not None:
                                    value.text = newRule[ 2 ][ 0 ]
                                else:
                                    xmltree.SubElement( rule, "value" ).text = newRule[ 2 ][ 0 ]
                                break
                                    
                    # Save the file
                    self.indent( root )
                    tree.write( filename, encoding="UTF-8" )
                    
                except:
                    print_exc()
    
                
                
    def deleteNodeRule( self, actionPath, originalRule ):
        dirs, files = xbmcvfs.listdir( actionPath )
        for file in files:
            if file == "index.xml":
                continue
            elif file.endswith( ".xml" ):
                filename = os.path.join( actionPath, file )
                
                # List the rules
                try:
                    # Load the xml file
                    tree = xmltree.parse( filename )
                    root = tree.getroot()
                    
                    # Look for any rules
                    rules = root.findall( "rule" )
                    if rules is not None:
                        for rule in rules:
                            value = rule.find( "value" )
                            if value is not None and value.text is not None:
                                translated = self.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), value.text ] )
                            else:
                                translated = self.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), "" ] )

                            if originalRule[ 0 ][ 1 ] == translated[ 0 ][ 1 ] and originalRule[ 1 ][ 0 ] == translated[ 1 ][ 0 ] and originalRule[ 2 ][ 0 ] == translated[ 2 ][ 0 ]:
                                # This is the right rule, delete it
                                root.remove( rule )
                                break
                                
                    # Save the file
                    self.indent( root )
                    tree.write( filename, encoding="UTF-8" )
                    
                except:
                    print_exc()
                    
    def isNodeRule( self, viewRule, actionPath ):
        if actionPath.endswith( "index.xml" ):
            return False
            
        if self.nodeRules is None:
            self.nodeRules = []
            # Load all the node rules for current directory
            ( filePath, fileName ) = os.path.split( actionPath )
            self.loadNodeRules( filePath )
        
        # If there are no node rules, return False
        if len( self.nodeRules ) == 0:
            return False

        # Compare the passed in rule with those in self.nodeRules
        count = 0
        for nodeRule in self.nodeRules:
            if nodeRule[0] == viewRule[0][1] and nodeRule[1] == viewRule[1][0] and nodeRule[2] == viewRule[2][0]:
                # Rule matches
                self.nodeRules.pop( count )
                return True
            count += 1
                
        return False
        
    def addAllNodeRules( self, actionPath, root ):
        if self.nodeRules is None:
            self.loadNodeRules( actionPath )
            
        if len( self.nodeRules ) == 0:
            return
            
        for nodeRule in self.nodeRules:
            rule = xmltree.SubElement( root, "rule" )
            rule.set( "field", nodeRule[ 0 ] )
            rule.set( "operator", nodeRule[ 1 ] )
            xmltree.SubElement( rule, "value" ).text = nodeRule[ 2 ]
    
    def loadNodeRules( self, actionPath ):
        log( "Loading node rules" )
        self.nodeRules = []
        # Load all the node rules for current directory
        actionPath = os.path.join( actionPath, "index.xml" )
        if xbmcvfs.exists( actionPath ):
            try:
                # Load the xml file
                tree = xmltree.parse( actionPath )
                root = tree.getroot()
                
                # Look for any rules
                rules = root.findall( "rule" )
                if rules is not None:
                    for rule in rules:
                        value = rule.find( "value" )
                        if value is not None and value.text is not None:
                            translated = self.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), value.text ] )
                        else:
                            translated = self.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), "" ] )
                            
                        # Save the rule
                        self.nodeRules.append( [ translated[0][1], translated[1][0], translated[2][0] ] )
            except:
                print_exc()
                
                
    # Functions for browsing for value
    def canBrowse( self, match, content = None ):
        # Check whether the match type allows browsing
        if content == "NONE":
            content = None
        
        # Load the rules
        tree = self._load_rules()
        
        elems = tree.getroot().find( "matches" ).findall( "match" )
        for elem in elems:
            if elem.attrib.get( "name" ) == match:
                canBrowse = elem.find( "browse" )
                if canBrowse is None:
                    # This match type is marked as non-browsable
                    return False
                if content is None:
                    # If we haven't been passed a content type, allow to browse all
                    return True
                    
                canBrowse = elem.find( content )
                if canBrowse is None:
                    # We can't browse for this content type
                    return False
                    
                # We can browse this content type
                return True
        return False
        
        
    def browse( self, actionPath, ruleNum, match, content = None ):
        # This function launches the browser for the given match and content type
        
        if content is None or content == "" or content == "NONE":
            if match != "path" and match != "playlist":
                # No content parameter passed, so check what contents are valid for
                # this type
                tree = self._load_rules()
                elems = tree.getroot().find( "matches" ).findall( "match" )
                matches = {}
                for elem in elems:
                    if elem.attrib.get( "name" ) == match:
                        matches["movies"] = elem.find( "movies" )
                        matches["tvshows"] = elem.find( "tvshows" )
                        matches["episodes"] = elem.find( "episodes" )
                        matches["musicvideos"] = elem.find( "musicvideos" )
                        
                        break
                        
                matchesList = []
                matchesValue = []
                # Generate a list of the available content types
                elems = tree.getroot().find( "content" ).findall( "type" )
                for elem in elems:
                    if matches[ elem.text ] is not None:
                        matchesList.append( xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) ) )
                        matchesValue.append( elem.text )

                if len( matchesList ) == 0:
                    log( "There are no valid content types for this match" )
                    return
                if len( matchesList ) == 1:
                    # Only one returned, no point offering a choice of content type
                    content = matchesValue[ 0 ]
                else:
                    # Display a select dialog so user can choose their content
                    selectedContent = xbmcgui.Dialog().select( __language__( 30308 ), matchesList )
            
                    # If the user selected nothing...
                    if selectedContent == -1:
                        return
                    
                    content = matchesValue[ selectedContent ]
                    
        if match == "title":
            self.createBrowseNode( content, None )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "tvshow":
            if content == "episodes":
                content = "tvshows"
            self.createBrowseNode( content, None )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "genres":
            self.createBrowseNode( content, "genres" )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "album":
            self.createBrowseNode( content, "none" )
            returnVal = self.browser( self.niceMatchName( match ) )

        if match == "country":
            self.createBrowseNode( content, "countries" )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "year":
            if content == "episodes":
                content = "tvshows"
            self.createBrowseNode( content, "years" )
            returnVal = self.browser( self.niceMatchName( match ) )
            
        if match == "artist":
            self.createBrowseNode( content, "artists" )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "director":
            self.createBrowseNode( content, "directors" )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "actor":
            if content == "episodes":
                content = "tvshows"
            self.createBrowseNode( content, "actors" )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "studios":
            self.createBrowseNode( content, "studios" )
            returnVal = self.browser( self.niceMatchName( match ) )

        if match == "path":
            returnVal = xbmcgui.Dialog().browse(0, self.niceMatchName( match ), "videos" )
                
        if match == "set":
            self.createBrowseNode( content, "sets" )
            returnVal = self.browser( self.niceMatchName( match ) )
                
        if match == "tag":
            self.createBrowseNode( content, "tags" )
            returnVal = self.browser( self.niceMatchName( match ) )
            
        if match == "playlist":
            returnVal = self.browserPlaylist( self.niceMatchName( match ) )
                
        try:
            log( "Selected: " + repr( returnVal ) )
            self.writeUpdatedRule( actionPath, ruleNum, value = returnVal.decode( "utf-8" ) )
        except:
            return
            
    def niceMatchName( self, match ):
        # This function retrieves the translated label for a given match
        tree = self._load_rules()
        elems = tree.getroot().find( "matches" ).findall( "match" )
        matches = {}
        for elem in elems:
            if elem.attrib.get( "name" ) == match:
                return xbmc.getLocalizedString( int( elem.find( "label" ).text ) )
                
    def createBrowseNode( self, content, grouping = None ):
        # This function creates a fake node which we'll use for browsing
        targetDir = os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", "video", "plugin.program.video.node.editor" )
        if not xbmcvfs.exists( targetDir ):
            xbmcvfs.mkdirs( targetDir )
            
        # Create a new etree
        tree = xmltree.ElementTree(xmltree.Element( "node" ) )
        root = tree.getroot()
        root.set( "type", "filter" )
        xmltree.SubElement( root, "label" ).text = "Fake node used for browsing"
        xmltree.SubElement( root, "content" ).text = content
        
        if grouping is not None:
            xmltree.SubElement( root, "group" ).text = grouping
        else:
            order = xmltree.SubElement( root, "order" )
            order.text = "sorttitle"
            order.set( "direction", "ascending" )
        
        self.indent( root )
        tree.write( os.path.join( targetDir, "temp.xml" ), encoding="UTF-8" )
        
    def deleteBrowseNode( self ):
        # Delete the fake node we used for browsing - not currently used as it breaks things
        shutil.rmtree( os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", "video", "plugin.program.video.node.editor" ) )
        
    def browser( self, title ):
        # Browser instance used by majority of browses
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail"], "directory": "library://video/plugin.program.video.node.editor/temp.xml", "media": "files" } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        
        
        listings = []
        values = []
            
        # Add all directories returned by the json query
        if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files'] is not None:
            for item in json_response['result']['files']:
                if item[ "label" ] == "..":
                    continue
                thumb = None
                if item[ "thumbnail" ] is not "":
                    thumb = item[ "thumbnail" ]
                listitem = xbmcgui.ListItem(label=item[ "label" ], iconImage=thumb )
                listitem.setProperty( "thumbnail", thumb )
                listings.append( listitem )
                values.append( item[ "label" ] )
            
        # Show dialog
        w = ShowDialog( "DialogSelect.xml", __cwd__, listing=listings, windowtitle=title )
        w.doModal()
        selectedItem = w.result
        del w
        
        if selectedItem == "" or selectedItem == -1:
            return None
        
        return values[ selectedItem ]
        
    def browserPlaylist( self, title ):
        # Browser instance used by majority of browses
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail"], "directory": "special://videoplaylists/", "media": "files" } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        
        listings = []
        values = []
            
        # Add all directories returned by the json query
        if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files'] is not None:
            for item in json_response['result']['files']:
                if item[ "label" ] == "..":
                    continue
                thumb = None
                if item[ "thumbnail" ] is not "":
                    thumb = item[ "thumbnail" ]
                listitem = xbmcgui.ListItem(label=item[ "label" ], iconImage=thumb )
                listitem.setProperty( "thumbnail", thumb )
                listings.append( listitem )
                values.append( item[ "label" ] )
            
        # Show dialog
        w = ShowDialog( "DialogSelect.xml", __cwd__, listing=listings, windowtitle=title )
        w.doModal()
        selectedItem = w.result
        del w
        
        if selectedItem == "" or selectedItem == -1:
            return None
        
        return values[ selectedItem ]
        


    
    # in-place prettyprint formatter
    def indent( self, elem, level=0 ):
        i = "\n" + level*"\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
                
# ============================
# === PRETTY SELECT DIALOG ===
# ============================
            
class ShowDialog( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.listing = kwargs.get( "listing" )
        self.windowtitle = kwargs.get( "windowtitle" )
        self.result = -1

    def onInit(self):
        try:
            self.fav_list = self.getControl(6)
            self.getControl(3).setVisible(False)
        except:
            print_exc()
            self.fav_list = self.getControl(3)

        self.getControl(5).setVisible(False)
        self.getControl(1).setLabel(self.windowtitle)

        for item in self.listing :
            listitem = xbmcgui.ListItem(label=item.getLabel(), label2=item.getLabel2(), iconImage=item.getProperty( "icon" ), thumbnailImage=item.getProperty( "thumbnail" ))
            listitem.setProperty( "Addon.Summary", item.getLabel2() )
            self.fav_list.addItem( listitem )

        self.setFocus(self.fav_list)

    def onAction(self, action):
        if action.getId() in ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.result = -1
            self.close()

    def onClick(self, controlID):
        if controlID == 6 or controlID == 3:
            num = self.fav_list.getSelectedPosition()
            self.result = num
        else:
            self.result = -1

        self.close()

    def onFocus(self, controlID):
        pass

