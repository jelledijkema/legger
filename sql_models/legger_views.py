def create_legger_views(session):
    session.execute(
        """
        DROP VIEW IF EXISTS hydroobjects_kenmerken3;
        """
    )

    session.execute(
        """
            CREATE VIEW hydroobjects_kenmerken3 AS 
            SELECT 
                h.id, 
                code, 
                categorieoppwaterlichaam, 
                streefpeil, 
                ABS(debiet) as debiet, 
                diepte, 
                breedte, 
                taludvoorkeur,
                begroeiingsvariant_id, 
                min_diepte, 
                max_diepte, 
                min_breedte, 
                max_breedte,
                ST_LENGTH("GEOMETRY") as lengte,
                geselecteerd_diepte,
                geselecteerd_breedte,
                geselecteerde_variant,
                geselecteerde_begroeiingsvariant,
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
                v.waterbreedte as geselecteerd_breedte,
                v.id as geselecteerde_variant,
                v.begroeiingsvariant_id as geselecteerde_begroeiingsvariant
                FROM geselecteerd g, varianten v
                WHERE g.variant_id = v.id) as sel
                ON sel.hydro_id = h.id       
        """)

    session.execute(
        """
        DELETE FROM views_geometry_columns WHERE view_name = 'hydroobjects_kenmerken3';
        """
    )

    session.execute(
        """
            INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, 
              f_geometry_column, read_only)
            VALUES('hydroobjects_kenmerken3', 'geometry', 'id', 'hydroobject', 'geometry', 1);         
        """)

    session.execute(
        """
            INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, 
              f_geometry_column, read_only)
            VALUES('hydroobjects_kenmerken3', 'line', 'id', 'hydroobject', 'geometry', 1);         
        """)

    session.commit()

    ### view for getting all legger results, including additional performance indicators

    session.execute(
        """
        DROP VIEW IF EXISTS hydroobjects_selected_legger;
        """
    )

    session.execute(
        """
            CREATE VIEW hydroobjects_selected_legger AS 
            SELECT 
                h.id, 
                h.code, 
                h.categorieoppwaterlichaam, 
                h.streefpeil, 
                h.debiet,
                k.diepte, 
                k.breedte, 
                k.taludvoorkeur, 
                ST_LENGTH(h.geometry) as lengte,
                h.geometry,
                s.selected_on as geselecteerd_op,
                --s.opmerkingen as selectie_opmerking,
                v.diepte as geselecteerde_diepte,
                v.waterbreedte as geselecteerd_waterbreedte,
                v.bodembreedte as geselecteerde_bodembreedte,
                v.talud as geselecteerd_talud,
                v.verhang_bos_bijkerk as verhang,
                v.opmerkingen as profiel_opmerking,
                p.t_fit as fit_score,
                p.t_afst as offset,
                p.t_overdiepte as overdiepte,
                p.t_overbreedte_l as overbreedte_links,
                p.t_overbreedte_r as overbreedte_rechts
            FROM hydroobject h
            JOIN kenmerken k ON h.id = k.hydro_id 	
            LEFT OUTER  JOIN geselecteerd s ON h.id = s.hydro_id
            LEFT OUTER JOIN varianten v ON s.variant_id = v.id
            LEFT OUTER JOIN profielfiguren p ON v.id = p.profid   
        """)

    session.execute(
        """
        DELETE FROM views_geometry_columns WHERE view_name = 'hydroobjects_selected_legger';
        """
    )

    session.execute(
        """
            INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, 
              f_geometry_column, read_only)
            VALUES('hydroobjects_selected_legger', 'geometry', 'id', 'hydroobject', 'geometry', 1);         
        """)


    session.commit()
