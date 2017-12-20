def create_legger_views(session):
    session.execute(
        """
        DROP VIEW IF EXISTS hydroobject_with_results;
        """
    )

    session.execute(
        """
            CREATE VIEW hydroobject_with_results AS
            SELECT *,
                   CASE WHEN t.qend > 0
                       THEN 1 ELSE 2
                   END AS direction
            FROM hydroobject h 
            JOIN tdi_hydro_object_results t ON h.objectid = t.hydroobject_id
            JOIN hydrokenmerken k ON h.objectid = k.objectid;        
        """)

    session.execute(
        """
        DELETE FROM views_geometry_columns WHERE view_name = 'hydroobject_with_results';
        """
    )

    session.execute(
        """
            INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, 
              f_geometry_column)
            VALUES('hydroobject_with_results', 'GEOMETRY', 'OGC_FID', 'hydroobject', 'GEOMETRY');         
        """)

    session.commit()
