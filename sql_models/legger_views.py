


def create_legger_views(session):

    session.execute(
        """
            CREATE VIEW IF NOT EXISTS hydroobject_with_results AS
            SELECT *
            FROM hydroobject h JOIN tdi_hydroobject_results t ON h.objectid = t.hydroobject_id;
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
