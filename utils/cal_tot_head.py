



"""
-- update verhang of single
UPDATE
	geselecteerd
SET
	hydro_verhang = (SELECT
		k.lengte * v.verhang / 1000 as hydro_verhang
	FROM hydroobject h
		INNER JOIN kenmerken k ON h.id = k.hydro_id
		INNER JOIN varianten v ON geselecteerd.variant_id = v.id
	WHERE geselecteerd.hydro_id =  h.id )

"""