def create_legger_views(session):
    session.execute(
        """
        DROP VIEW IF EXISTS hydroobjects_kenmerken;
        """
    )

    session.execute(
        """
            CREATE VIEW hydroobjects_kenmerken15 AS 
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

    # SELECT
    # AddGeometryColumn('hydroobject', 'line', 28992, 'LINESTRING', 2)
    # UPDATE hydroobject set line = MakeLine(SNAPTOGRID(StartPoint("GEOMETRY"),0.1), SNAPTOGRID(EndPoint("GEOMETRY"),  0.1))
    # SELECT CreateSpatialIndex('hydroobject', 'line')



    # # totaal netwerk  ==> not needed. duikers already part of hydrovakken
    # session.execute(
    #     """
    #     DROP VIEW IF EXISTS totaal_netwerk_view;
    #     """
    # )
    #
    # session.execute(
    #     """
    #     CREATE VIEW totaal_netwerk_view AS
    #     SELECT id, categorieoppwaterlichaam, GEOMETRY, direction, debiet, lengte, hydro_id, streefpeil, diepte, bron_diepte, bodemhoogte, breedte, bron_breedte, taludvoorkeur, grondsoort, bron_grondsoort,
    #     min_diepte, max_diepte, min_breedte, max_breedte
    #     FROM hydroobjects_kenmerken
    #     UNION ALL
    #     SELECT id, "5" AS categorieoppwaterlichaam, GEOMETRY, 3 AS direction, debiet, lengte, NULL AS hydr_id, NULL AS streefpeil, NULL AS diepte, NULL AS bron_diepte, NULL AS bodemhoogte,
    #     NULL AS breedte, NULL AS bron_breedte, NULL AS taludvoorkeur, NULL AS grondsoort, NULL AS bron_grondsoort,
    #     NULL AS min_diepte, NULL AS max_diepte, NULL AS min_breedte, NULL AS max_breedte
    #     FROM duikersifonhevel
    #     """)
    #
    # session.execute(
    #     """
    #     DELETE FROM geometry_columns WHERE view_name = 'totaal_netwerk_view';
    #     """
    # )
    #
    # session.execute(
    #     """
    #         INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name,
    #           f_geometry_column, read_only)
    #         VALUES('totaal_netwerk_view', 'geometry', 'id', 'hydroobject', 'geometry', 1);
    #     """)
    #
    # session.commit()
