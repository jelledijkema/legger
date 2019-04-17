def snap_points(db_cursor):
    db_cursor.executescript("""
    -- maak alle begin en eindpunten
        DROP TABLE IF EXISTS nodes
        ;
        
        CREATE TABLE nodes AS
        SELECT ST_Startpoint(GEOMETRY) AS geometry, id, 'start' as type, CreateUUID() as uuid
        FROM hydroobject
        UNION ALL
        SELECT ST_Endpoint(GEOMETRY) AS geometry, id, 'end' as type, CreateUUID() as uuid
        FROM hydroobject
        ;
        
        -- registreer de geometry (alleen bij debuggen)
        --SELECT RecoverGeometryColumn( 'nodes' , 'geometry' , 28992 , 'POINT' );
        
        -- koppel bein en eindpunten die binnen 50 cm van elkaar liggen
        DROP TABLE IF EXISTS nodes_join
        ;
        
        CREATE TABLE nodes_join AS
        SELECT a.*, b.uuid as target
        FROM nodes as a
        LEFT JOIN nodes as b
        ON ST_Distance(a.geometry,b.geometry) < 0.5
        ORDER BY b.uuid
        ;
        
        -- registreer de geometry (alleen bij debuggen)
        --SELECT RecoverGeometryColumn( 'nodes_join' , 'geometry' , 28992 , 'POINT' );
        
        -- maak nieuwe bgin en eindpunten, neem er willekeurig eenje die de ander(e) vervangt
        DROP TABLE IF EXISTS nodes_new
        ;
        
        CREATE TABLE nodes_new AS
        WITH aggre AS (
        SELECT DISTINCT uuid, MIN(target) as replace, geometry
        FROM nodes_join
        GROUP BY uuid, geometry
        )
        SELECT a.replace, a.uuid, b.geometry as newgeom
        FROM aggre as a
        LEFT JOIN nodes as b
        ON a.replace = b.uuid
        ;
        
        -- registreer de geometry (alleen bij debuggen)
        --SELECT RecoverGeometryColumn( 'nodes_new' , 'newgeom' , 28992 , 'POINT' )
        
        -- update de begin en eindpunten
        UPDATE nodes
        set geometry = (
        SELECT newgeom
        FROM nodes_new
        WHERE uuid = nodes.uuid
        )
        WHERE EXISTS (SELECT newgeom
        FROM nodes_new
        WHERE uuid = nodes.uuid
        )
        ;
        
        -- vervang de bein en eindpunten in de hydroobjecten
        UPDATE hydroobject
        SET geometry = SetStartPoint(geometry,
        (SELECT geometry
        FROM nodes
        WHERE id = hydroobject.id
        AND type = 'start'
        ))
        WHERE EXISTS (SELECT geometry
        FROM nodes
        WHERE id = hydroobject.id
        AND type = 'start'
        )
        ;
        UPDATE hydroobject
        SET geometry = SetEndPoint(geometry,
        (SELECT geometry
        FROM nodes
        WHERE id = hydroobject.id
        AND type = 'end'
        ))
        WHERE EXISTS (SELECT geometry
        FROM nodes
        WHERE id = hydroobject.id
        AND type = 'end'
        )
        ;
        
        -- ruim de rommel op
        DROP TABLE IF EXISTS nodes
        ;
        DROP TABLE IF EXISTS nodes_join
        ;
        DROP TABLE IF EXISTS nodes_new
        ;
    """)
    db_cursor.execute('vacuum')

    return
