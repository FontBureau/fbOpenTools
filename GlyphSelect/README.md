<img src="https://github.com/FontBureau/fbOpenTools/raw/master/GlyphSelect/GlyphSelect_preview.png" />



    <p>Search for glyphs using a variety of parameters:</p>
    
    <dl>
    
    <dt>Glyph Name:</dt>
        <dd>Exact match for glyph name.</dd>
    
    <dt>Base Name:</dt>
        <dd>Exact match for the basename of the glyph (anything before the first period in a glyph name)</dd>
    
    <dt>Suffix</dt>
        <dd>Exact match for the suffix of the glyph name (anything after the first period).</dd>

    <dt>Unicode value</dt>
        <dd>Find exact match for hexadecimal unicode value.</dd>
    
    <dt>Unicode category</dt>
        <dd>The unicode category groups and individual categories are listed in a dropdown.<br /> 
        You might have to hit enter/return in the dropdown to select an item.
        These categories are inclusive, so they will match base glyphs and alternates ("number" will match 'zero' and also 'zero.sups').</dd> 

    <p>You can use the following wildcards:</p>
        <dl>
        <dt>*</dt>	<dd>matches everything</dd>
        <dt>?</dt>	<dd>matches any single character</dd>
        <dt>[seq]</dt>	<dd>matches any character in seq</dd>
        <dt>[!seq]</dt>	<dd>matches any character not in seq</dd>
        </dl>

    <p>Then you can manually select glyphs (by default, all search results are selected)</p>

    <p>You can perform the following selection manipulations in the current font or in all open fonts:</p>

    <ul>
    <li>Replace selection with results</li>
    <li>Add results to selection</li>
    <li>Subtract results from selection</li>
    <li>Intersect results and seletion (select glyphs common to both) </li>
    <li>Print the glyph list to the output window.</li>
    </ul>
    
<p>This is released under the MIT license. See the the html file inside the extension for more information.</p>
