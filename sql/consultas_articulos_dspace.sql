-- lista de articulos
-- ~ comm ID	Articulo	Autor	Subtematica	PalabrasClaves	Fecha

SELECT 
    facultad.hdl_comm AS comm,
	item.handle AS ID,
	item.item_name AS Articulo, 
	autor.lista_autores AS Autor,
	facultad.community_name AS Subcomunidad,
	palabra_clave.palabras_clave AS PalabrasClaves,
	fecha.fecha AS Fecha
FROM 
	(
		-- ~ facultades o revistas
		SELECT 
            REPLACE(h.handle,'123456789/','comm') AS hdl_comm,
			cc.child_comm_id AS comm,
			mv.metadata_field_id AS f_id,
			mv.text_value AS community_name
		FROM 
			community2community cc, 
			handle h,
			metadatavalue mv
		WHERE 
			( h.handle = '123456789/1' OR h.handle = '123456789/4105' )
			AND h.resource_id = cc.parent_comm_id 
			AND cc.child_comm_id = mv.dspace_object_id
			AND mv.metadata_field_id = 70
	) AS facultad,
	(	
		-- ~ articulos
		SELECT 
			cc.community_id as comm,
			ci.collection_id AS coll, 
			ci.item_id AS item_id, 
			SUBSTRING(h.handle FROM 11) AS handle,
			mv.metadata_field_id AS f_id,
			mv.text_value AS item_name
		FROM 
			community2collection cc, 
			collection2item ci,
            item i,
			handle h,
			metadatavalue mv
		WHERE 
			cc.collection_id = ci.collection_id 
            AND ci.item_id = i.uuid 
            AND i.in_archive = true AND i.withdrawn = false
			AND ci.item_id = h.resource_id 
			AND ci.item_id =  mv.dspace_object_id
			AND mv.metadata_field_id = 70
			AND mv.text_value NOT LIKE 'Información%%'
			AND mv.text_value NOT LIKE 'Grupo de Investigación%%'
	) AS item, 
	(
		-- ~ fecha de ingreso
		SELECT 
			mv.dspace_object_id AS item_id,
			SPLIT_PART(mv.text_value, 'T', 1) AS fecha
		FROM 
			metadatavalue mv
		WHERE 
			mv.metadata_field_id = 17 	
	) AS fecha,
	(
		-- ~ palabras clave
		SELECT 
			t.item_id AS item_id,
			COUNT(item_id) AS total_palabras_clave,
			STRING_AGG(t.palabra_clave, ';') AS palabras_clave
		FROM (
			SELECT 
				mv.dspace_object_id AS item_id,
				mv.place,
				mv.text_value AS palabra_clave
			FROM 
				metadatavalue mv
			WHERE 
				mv.metadata_field_id = 63 
			ORDER BY 
				mv.dspace_object_id, mv.place
				
		) AS t
		GROUP BY 
			t.item_id
	) AS palabra_clave,
	(
		-- ~ autores
		SELECT 
			t.item_id,
			COUNT(item_id) AS total_autores,
			STRING_AGG(t.author_name, ';') AS lista_autores
		FROM (
			SELECT 
				mv.dspace_object_id AS item_id,
				mv.place,
				mv.text_value AS author_name
			FROM 
				metadatavalue mv
			WHERE 
				mv.metadata_field_id = 9 
			ORDER BY 
				mv.dspace_object_id, mv.place
				
		) AS t
		GROUP BY 
			t.item_id
	) AS autor
WHERE
	facultad.comm = item.comm
	AND item.item_id = fecha.item_id
	AND item.item_id = palabra_clave.item_id
	AND item.item_id = autor.item_id
