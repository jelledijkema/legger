<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" labelsEnabled="1" version="3.10.6-A Coruña" simplifyLocal="1" minScale="1e+08" readOnly="0" maxScale="0" simplifyDrawingHints="1" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" simplifyMaxScale="1" simplifyDrawingTol="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="RuleRenderer" forceraster="0" enableorderby="0" symbollevels="0">
    <rules key="{6c95b972-c884-47bd-b670-7c570711d0e9}">
      <rule label="gekozen" filter=" &quot;geselecteerd_diepte&quot; IS NOT NULL" symbol="0" key="{0eb0c1c3-6a71-4167-ba45-1c1f04964a7d}"/>
      <rule label="nog kiezen" filter=" &quot;geselecteerd_diepte&quot; IS NULL" symbol="1" key="{988a68ea-4d60-42ea-bb80-cb766f07f6cf}"/>
    </rules>
    <symbols>
      <symbol type="line" clip_to_extent="1" force_rhr="0" alpha="1" name="0">
        <layer pass="0" class="SimpleLine" enabled="1" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="178,223,138,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="0.66" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="ring_filter"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option name="properties"/>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="line" clip_to_extent="1" force_rhr="0" alpha="1" name="1">
        <layer pass="0" class="SimpleLine" enabled="1" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="253,191,111,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="1.66" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="ring_filter"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option name="properties"/>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style useSubstitutions="0" namedStyle="Standaard" textOrientation="horizontal" fontCapitals="0" fontWeight="50" fontKerning="1" fontSizeUnit="Point" fieldName="'streefpeil: ' || round(&quot;streefpeil&quot;,2)" fontWordSpacing="0" fontUnderline="0" textColor="0,0,0,255" fontStrikeout="0" fontLetterSpacing="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" isExpression="1" fontSize="8.25" fontItalic="0" multilineHeight="1" previewBkgrdColor="255,255,255,255" textOpacity="1" blendMode="0" fontFamily="MS Shell Dlg 2">
        <text-buffer bufferOpacity="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferJoinStyle="128" bufferColor="255,255,255,255" bufferNoFill="0" bufferBlendMode="0" bufferSize="1" bufferDraw="1" bufferSizeUnits="MM"/>
        <background shapeSizeUnit="MM" shapeSizeType="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeSVGFile="" shapeJoinStyle="64" shapeOffsetUnit="MM" shapeBorderColor="128,128,128,255" shapeDraw="0" shapeBorderWidthUnit="MM" shapeRadiiUnit="MM" shapeRotationType="0" shapeOffsetX="0" shapeOffsetY="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeRotation="0" shapeRadiiX="0" shapeRadiiY="0" shapeOpacity="1" shapeBlendMode="0" shapeFillColor="255,255,255,255" shapeType="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeX="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSizeY="0" shapeBorderWidth="0">
          <symbol type="marker" clip_to_extent="1" force_rhr="0" alpha="1" name="markerSymbol">
            <layer pass="0" class="SimpleMarker" enabled="1" locked="0">
              <prop v="0" k="angle"/>
              <prop v="225,89,137,255" k="color"/>
              <prop v="1" k="horizontal_anchor_point"/>
              <prop v="bevel" k="joinstyle"/>
              <prop v="circle" k="name"/>
              <prop v="0,0" k="offset"/>
              <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
              <prop v="MM" k="offset_unit"/>
              <prop v="35,35,35,255" k="outline_color"/>
              <prop v="solid" k="outline_style"/>
              <prop v="0" k="outline_width"/>
              <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
              <prop v="MM" k="outline_width_unit"/>
              <prop v="diameter" k="scale_method"/>
              <prop v="2" k="size"/>
              <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
              <prop v="MM" k="size_unit"/>
              <prop v="1" k="vertical_anchor_point"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" name="name" value=""/>
                  <Option name="properties"/>
                  <Option type="QString" name="type" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowOffsetAngle="135" shadowOffsetGlobal="1" shadowRadiusUnit="MM" shadowScale="100" shadowOffsetUnit="MM" shadowRadius="1.5" shadowOpacity="0.7" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowDraw="0" shadowUnder="0" shadowBlendMode="6" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusAlphaOnly="0" shadowColor="0,0,0,255" shadowOffsetDist="1"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" name="name" value=""/>
            <Option name="properties"/>
            <Option type="QString" name="type" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format reverseDirectionSymbol="0" placeDirectionSymbol="0" formatNumbers="1" rightDirectionSymbol=">" useMaxLineLengthForAutoWrap="1" multilineAlign="4294967295" decimals="2" wrapChar="" leftDirectionSymbol="&lt;" autoWrapLength="0" plussign="0" addDirectionSymbol="0"/>
      <placement overrunDistance="0" geometryGeneratorType="PointGeometry" rotationAngle="0" maxCurvedCharAngleOut="-25" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MapUnit" geometryGeneratorEnabled="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" centroidInside="0" preserveRotation="1" distMapUnitScale="3x:0,0,0,0,0,0" priority="5" repeatDistance="0" overrunDistanceUnit="MM" geometryGenerator="" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" layerType="LineGeometry" yOffset="0" xOffset="0" repeatDistanceUnits="MM" placementFlags="15" maxCurvedCharAngleIn="25" placement="2" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" fitInPolygonOnly="0" offsetType="0" dist="0" quadOffset="4" distUnits="MM" centroidWhole="0"/>
      <rendering obstacle="1" limitNumLabels="0" labelPerPart="0" maxNumLabels="2000" scaleMax="5000" displayAll="0" fontLimitPixelSize="0" drawLabels="1" zIndex="0" obstacleFactor="1" fontMaxPixelSize="10000" scaleMin="1" obstacleType="0" fontMinPixelSize="3" minFeatureSize="0" scaleVisibility="1" upsidedownLabels="0" mergeLines="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" name="name" value=""/>
          <Option name="properties"/>
          <Option type="QString" name="type" value="collection"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option type="QString" name="anchorPoint" value="pole_of_inaccessibility"/>
          <Option type="Map" name="ddProperties">
            <Option type="QString" name="name" value=""/>
            <Option name="properties"/>
            <Option type="QString" name="type" value="collection"/>
          </Option>
          <Option type="bool" name="drawToAllParts" value="false"/>
          <Option type="QString" name="enabled" value="0"/>
          <Option type="QString" name="lineSymbol" value="&lt;symbol type=&quot;line&quot; clip_to_extent=&quot;1&quot; force_rhr=&quot;0&quot; alpha=&quot;1&quot; name=&quot;symbol&quot;>&lt;layer pass=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot; locked=&quot;0&quot;>&lt;prop v=&quot;square&quot; k=&quot;capstyle&quot;/>&lt;prop v=&quot;5;2&quot; k=&quot;customdash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;customdash_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;customdash_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;draw_inside_polygon&quot;/>&lt;prop v=&quot;bevel&quot; k=&quot;joinstyle&quot;/>&lt;prop v=&quot;60,60,60,255&quot; k=&quot;line_color&quot;/>&lt;prop v=&quot;solid&quot; k=&quot;line_style&quot;/>&lt;prop v=&quot;0.3&quot; k=&quot;line_width&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;line_width_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;ring_filter&quot;/>&lt;prop v=&quot;0&quot; k=&quot;use_custom_dash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;width_map_unit_scale&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; name=&quot;name&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; name=&quot;type&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
          <Option type="double" name="minLength" value="0"/>
          <Option type="QString" name="minLengthMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="minLengthUnit" value="MM"/>
          <Option type="double" name="offsetFromAnchor" value="0"/>
          <Option type="QString" name="offsetFromAnchorMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="offsetFromAnchorUnit" value="MM"/>
          <Option type="double" name="offsetFromLabel" value="0"/>
          <Option type="QString" name="offsetFromLabelMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="offsetFromLabelUnit" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <property key="dualview/previewExpressions">
      <value>COALESCE("OGC_FID", '&lt;NULL>')</value>
    </property>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory width="15" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minScaleDenominator="0" maxScaleDenominator="1e+08" opacity="1" penColor="#000000" minimumSize="0" penAlpha="255" barWidth="5" scaleBasedVisibility="0" lineSizeType="MM" scaleDependency="Area" diagramOrientation="Up" sizeType="MM" backgroundColor="#ffffff" lineSizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" height="15" enabled="0" labelPlacementMethod="XHeight" penWidth="0">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" field="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="2" placement="2" showAll="1" dist="0" priority="0" zIndex="0" obstacle="0">
    <properties>
      <Option type="Map">
        <Option type="QString" name="name" value=""/>
        <Option name="properties"/>
        <Option type="QString" name="type" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="code">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="categorieoppwaterlichaam">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="streefpeil">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="debiet">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="debiet_3di">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="debiet_aangepast">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="diepte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="breedte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="taludvoorkeur">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="begroeiingsvariant_id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="min_diepte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="max_diepte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="min_breedte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="max_breedte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="lengte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geselecteerd_diepte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geselecteerd_breedte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geselecteerde_variant">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geselecteerde_begroeiingsvariant">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geselecteerd_verhang">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="opmerkingen">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="kijkp_breedte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="kijkp_diepte">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="kijkp_talud">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="kijkp_reden">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="line">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="direction">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="reversed">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" field="id" index="0"/>
    <alias name="" field="code" index="1"/>
    <alias name="" field="categorieoppwaterlichaam" index="2"/>
    <alias name="" field="streefpeil" index="3"/>
    <alias name="" field="debiet" index="4"/>
    <alias name="" field="debiet_3di" index="5"/>
    <alias name="" field="debiet_aangepast" index="6"/>
    <alias name="" field="diepte" index="7"/>
    <alias name="" field="breedte" index="8"/>
    <alias name="" field="taludvoorkeur" index="9"/>
    <alias name="" field="begroeiingsvariant_id" index="10"/>
    <alias name="" field="min_diepte" index="11"/>
    <alias name="" field="max_diepte" index="12"/>
    <alias name="" field="min_breedte" index="13"/>
    <alias name="" field="max_breedte" index="14"/>
    <alias name="" field="lengte" index="15"/>
    <alias name="" field="geselecteerd_diepte" index="16"/>
    <alias name="" field="geselecteerd_breedte" index="17"/>
    <alias name="" field="geselecteerde_variant" index="18"/>
    <alias name="" field="geselecteerde_begroeiingsvariant" index="19"/>
    <alias name="" field="geselecteerd_verhang" index="20"/>
    <alias name="" field="opmerkingen" index="21"/>
    <alias name="" field="kijkp_breedte" index="22"/>
    <alias name="" field="kijkp_diepte" index="23"/>
    <alias name="" field="kijkp_talud" index="24"/>
    <alias name="" field="kijkp_reden" index="25"/>
    <alias name="" field="line" index="26"/>
    <alias name="" field="direction" index="27"/>
    <alias name="" field="reversed" index="28"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" field="id" applyOnUpdate="0"/>
    <default expression="" field="code" applyOnUpdate="0"/>
    <default expression="" field="categorieoppwaterlichaam" applyOnUpdate="0"/>
    <default expression="" field="streefpeil" applyOnUpdate="0"/>
    <default expression="" field="debiet" applyOnUpdate="0"/>
    <default expression="" field="debiet_3di" applyOnUpdate="0"/>
    <default expression="" field="debiet_aangepast" applyOnUpdate="0"/>
    <default expression="" field="diepte" applyOnUpdate="0"/>
    <default expression="" field="breedte" applyOnUpdate="0"/>
    <default expression="" field="taludvoorkeur" applyOnUpdate="0"/>
    <default expression="" field="begroeiingsvariant_id" applyOnUpdate="0"/>
    <default expression="" field="min_diepte" applyOnUpdate="0"/>
    <default expression="" field="max_diepte" applyOnUpdate="0"/>
    <default expression="" field="min_breedte" applyOnUpdate="0"/>
    <default expression="" field="max_breedte" applyOnUpdate="0"/>
    <default expression="" field="lengte" applyOnUpdate="0"/>
    <default expression="" field="geselecteerd_diepte" applyOnUpdate="0"/>
    <default expression="" field="geselecteerd_breedte" applyOnUpdate="0"/>
    <default expression="" field="geselecteerde_variant" applyOnUpdate="0"/>
    <default expression="" field="geselecteerde_begroeiingsvariant" applyOnUpdate="0"/>
    <default expression="" field="geselecteerd_verhang" applyOnUpdate="0"/>
    <default expression="" field="opmerkingen" applyOnUpdate="0"/>
    <default expression="" field="kijkp_breedte" applyOnUpdate="0"/>
    <default expression="" field="kijkp_diepte" applyOnUpdate="0"/>
    <default expression="" field="kijkp_talud" applyOnUpdate="0"/>
    <default expression="" field="kijkp_reden" applyOnUpdate="0"/>
    <default expression="" field="line" applyOnUpdate="0"/>
    <default expression="" field="direction" applyOnUpdate="0"/>
    <default expression="" field="reversed" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="id" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="code" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="categorieoppwaterlichaam" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="streefpeil" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="debiet" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="debiet_3di" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="debiet_aangepast" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="diepte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="breedte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="taludvoorkeur" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="begroeiingsvariant_id" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="min_diepte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="max_diepte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="min_breedte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="max_breedte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="lengte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="geselecteerd_diepte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="geselecteerd_breedte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="geselecteerde_variant" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="geselecteerde_begroeiingsvariant" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="geselecteerd_verhang" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="opmerkingen" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="kijkp_breedte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="kijkp_diepte" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="kijkp_talud" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="kijkp_reden" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="line" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="direction" notnull_strength="0"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" field="reversed" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="id"/>
    <constraint exp="" desc="" field="code"/>
    <constraint exp="" desc="" field="categorieoppwaterlichaam"/>
    <constraint exp="" desc="" field="streefpeil"/>
    <constraint exp="" desc="" field="debiet"/>
    <constraint exp="" desc="" field="debiet_3di"/>
    <constraint exp="" desc="" field="debiet_aangepast"/>
    <constraint exp="" desc="" field="diepte"/>
    <constraint exp="" desc="" field="breedte"/>
    <constraint exp="" desc="" field="taludvoorkeur"/>
    <constraint exp="" desc="" field="begroeiingsvariant_id"/>
    <constraint exp="" desc="" field="min_diepte"/>
    <constraint exp="" desc="" field="max_diepte"/>
    <constraint exp="" desc="" field="min_breedte"/>
    <constraint exp="" desc="" field="max_breedte"/>
    <constraint exp="" desc="" field="lengte"/>
    <constraint exp="" desc="" field="geselecteerd_diepte"/>
    <constraint exp="" desc="" field="geselecteerd_breedte"/>
    <constraint exp="" desc="" field="geselecteerde_variant"/>
    <constraint exp="" desc="" field="geselecteerde_begroeiingsvariant"/>
    <constraint exp="" desc="" field="geselecteerd_verhang"/>
    <constraint exp="" desc="" field="opmerkingen"/>
    <constraint exp="" desc="" field="kijkp_breedte"/>
    <constraint exp="" desc="" field="kijkp_diepte"/>
    <constraint exp="" desc="" field="kijkp_talud"/>
    <constraint exp="" desc="" field="kijkp_reden"/>
    <constraint exp="" desc="" field="line"/>
    <constraint exp="" desc="" field="direction"/>
    <constraint exp="" desc="" field="reversed"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column type="field" name="code" hidden="0" width="-1"/>
      <column type="field" name="categorieoppwaterlichaam" hidden="0" width="-1"/>
      <column type="actions" hidden="1" width="-1"/>
      <column type="field" name="id" hidden="0" width="-1"/>
      <column type="field" name="streefpeil" hidden="0" width="-1"/>
      <column type="field" name="debiet" hidden="0" width="-1"/>
      <column type="field" name="diepte" hidden="0" width="-1"/>
      <column type="field" name="breedte" hidden="0" width="-1"/>
      <column type="field" name="lengte" hidden="0" width="-1"/>
      <column type="field" name="taludvoorkeur" hidden="0" width="-1"/>
      <column type="field" name="direction" hidden="0" width="-1"/>
      <column type="field" name="debiet_3di" hidden="0" width="-1"/>
      <column type="field" name="debiet_aangepast" hidden="0" width="-1"/>
      <column type="field" name="begroeiingsvariant_id" hidden="0" width="-1"/>
      <column type="field" name="min_diepte" hidden="0" width="-1"/>
      <column type="field" name="max_diepte" hidden="0" width="-1"/>
      <column type="field" name="min_breedte" hidden="0" width="-1"/>
      <column type="field" name="max_breedte" hidden="0" width="-1"/>
      <column type="field" name="geselecteerd_diepte" hidden="0" width="248"/>
      <column type="field" name="geselecteerd_breedte" hidden="0" width="234"/>
      <column type="field" name="geselecteerde_variant" hidden="0" width="177"/>
      <column type="field" name="geselecteerde_begroeiingsvariant" hidden="0" width="-1"/>
      <column type="field" name="opmerkingen" hidden="0" width="-1"/>
      <column type="field" name="line" hidden="0" width="-1"/>
      <column type="field" name="reversed" hidden="0" width="-1"/>
      <column type="field" name="geselecteerd_verhang" hidden="0" width="252"/>
      <column type="field" name="kijkp_breedte" hidden="0" width="-1"/>
      <column type="field" name="kijkp_diepte" hidden="0" width="-1"/>
      <column type="field" name="kijkp_talud" hidden="0" width="-1"/>
      <column type="field" name="kijkp_reden" hidden="0" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1">.</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>.</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
Formulieren van QGIS kunnen een functie voor Python hebben die wordt aangeroepen wanneer het formulier wordt geopend.

Gebruik deze functie om extra logica aan uw formulieren toe te voegen.

Voer de naam van de functie in in het veld "Python Init function".

Een voorbeeld volgt hieronder:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="begroeiingsvariant_id" editable="1"/>
    <field name="breedte" editable="1"/>
    <field name="categorieoppwaterlichaam" editable="1"/>
    <field name="code" editable="1"/>
    <field name="debiet" editable="1"/>
    <field name="debiet_3di" editable="1"/>
    <field name="debiet_aangepast" editable="1"/>
    <field name="diepte" editable="1"/>
    <field name="direction" editable="1"/>
    <field name="geselecteerd_breedte" editable="1"/>
    <field name="geselecteerd_diepte" editable="1"/>
    <field name="geselecteerd_verhang" editable="1"/>
    <field name="geselecteerde_begroeiingsvariant" editable="1"/>
    <field name="geselecteerde_variant" editable="1"/>
    <field name="id" editable="1"/>
    <field name="kijkp_breedte" editable="1"/>
    <field name="kijkp_diepte" editable="1"/>
    <field name="kijkp_reden" editable="1"/>
    <field name="kijkp_talud" editable="1"/>
    <field name="lengte" editable="1"/>
    <field name="line" editable="1"/>
    <field name="max_breedte" editable="1"/>
    <field name="max_diepte" editable="1"/>
    <field name="min_breedte" editable="1"/>
    <field name="min_diepte" editable="1"/>
    <field name="opmerkingen" editable="1"/>
    <field name="reversed" editable="1"/>
    <field name="streefpeil" editable="1"/>
    <field name="taludvoorkeur" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="begroeiingsvariant_id"/>
    <field labelOnTop="0" name="breedte"/>
    <field labelOnTop="0" name="categorieoppwaterlichaam"/>
    <field labelOnTop="0" name="code"/>
    <field labelOnTop="0" name="debiet"/>
    <field labelOnTop="0" name="debiet_3di"/>
    <field labelOnTop="0" name="debiet_aangepast"/>
    <field labelOnTop="0" name="diepte"/>
    <field labelOnTop="0" name="direction"/>
    <field labelOnTop="0" name="geselecteerd_breedte"/>
    <field labelOnTop="0" name="geselecteerd_diepte"/>
    <field labelOnTop="0" name="geselecteerd_verhang"/>
    <field labelOnTop="0" name="geselecteerde_begroeiingsvariant"/>
    <field labelOnTop="0" name="geselecteerde_variant"/>
    <field labelOnTop="0" name="id"/>
    <field labelOnTop="0" name="kijkp_breedte"/>
    <field labelOnTop="0" name="kijkp_diepte"/>
    <field labelOnTop="0" name="kijkp_reden"/>
    <field labelOnTop="0" name="kijkp_talud"/>
    <field labelOnTop="0" name="lengte"/>
    <field labelOnTop="0" name="line"/>
    <field labelOnTop="0" name="max_breedte"/>
    <field labelOnTop="0" name="max_diepte"/>
    <field labelOnTop="0" name="min_breedte"/>
    <field labelOnTop="0" name="min_diepte"/>
    <field labelOnTop="0" name="opmerkingen"/>
    <field labelOnTop="0" name="reversed"/>
    <field labelOnTop="0" name="streefpeil"/>
    <field labelOnTop="0" name="taludvoorkeur"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>COALESCE("OGC_FID", '&lt;NULL>')</previewExpression>
  <mapTip>OGC_FID</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
