def create_legger_views(session):
    session.execute(
        """
        DROP VIEW IF EXISTS hydroobjects_kenmerken;
        """
    )

    session.execute(
        """
            CREATE VIEW hydroobjects_kenmerken AS
            SELECT *,
                   CASE WHEN h.debiet > 0
                       THEN 1 ELSE 2
                   END AS direction
            FROM hydroobject h 
            JOIN kenmerken k ON h.id = k.hydro_id;        
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
            VALUES('hydroobjects_kenmerken', 'geometry', 'id', 'hydroobject', 'geometry', 1);         
        """)

    session.commit()
