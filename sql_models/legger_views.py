def create_legger_views(session):
    session.execute(
        """
        DROP VIEW IF EXISTS hydroobjects_kenmerken;
        """
    )

    session.execute(
        """
            CREATE VIEW hydroobjects_kenmerken AS 
            SELECT 
                h.objectid, 
                h.id, 
                code, 
                categorieoppwaterlichaam, 
                streefpeil, 
                ABS(debiet) as debiet, 
                diepte, 
                breedte, 
                taludvoorkeur, 
                min_diepte, 
                max_diepte, 
                min_breedte, 
                max_breedte,
                ST_LENGTH("GEOMETRY") as lengte,
                geselecteerd_diepte,
                geselecteerd_breedte,
                CASE 
                  WHEN h.debiet >= 0 THEN "GEOMETRY"
                  WHEN h.debiet THEN ST_REVERSE("GEOMETRY")
                    ELSE "GEOMETRY" 
                END AS "GEOMETRY",
                CASE 
                  WHEN h.debiet >= 0 THEN MakeLine(StartPoint("GEOMETRY"), EndPoint("GEOMETRY"))
                  WHEN h.debiet THEN MakeLine(EndPoint("GEOMETRY"), StartPoint("GEOMETRY"))
                    ELSE MakeLine(StartPoint("GEOMETRY"), EndPoint("GEOMETRY"))
                END AS line,
                CASE WHEN h.debiet > 0 THEN 1
                    WHEN h.debiet  THEN 1
                    ELSE 3 
                END AS direction,
                CASE WHEN h.debiet >= 0 THEN CAST(0 AS BIT)
                    WHEN h.debiet  THEN CAST(1 AS BIT)
                    ELSE null 
                END AS reversed
            FROM hydroobject h 
            JOIN kenmerken k ON h.id = k.hydro_id 
            LEFT OUTER JOIN ( 
                SELECT
                hydro_id,
                min(diepte) AS min_diepte,
                max(diepte) AS max_diepte,
                min(waterbreedte) AS min_breedte,
                max(waterbreedte) AS max_breedte
                FROM varianten
                GROUP BY hydro_id) AS mm 
                ON mm.hydro_id = h.id
            LEFT OUTER JOIN (
                SELECT
                g.hydro_id,
                v.diepte as geselecteerd_diepte,
                v.waterbreedte as geselecteerd_breedte
                FROM geselecteerd g, varianten v
                WHERE	g.variant_id = v.id) as sel
                ON sel.hydro_id = h.id       
        """)

    session.execute(
        """
        DELETE FROM views_geometry_columns WHERE view_name = 'hydroobjects_kenmerken';
        """
    )

    session.execute(
        """
            INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, 
              f_geometry_column, read_only)
            VALUES('hydroobjects_kenmerken', 'geometry', 'objectid', 'hydroobject', 'geometry', 1);         
        """)

    session.execute(
        """
            INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, 
              f_geometry_column, read_only)
            VALUES('hydroobjects_kenmerken', 'line', 'objectid', 'hydroobject', 'geometry', 1);         
        """)

    session.commit()
