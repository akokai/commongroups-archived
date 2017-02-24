-- THIS IS NOT A SCRIPT
-- This is where I have been composing SQL commands to test them out.

-- -- Read tab-separated values from file, ignore header
-- create table dtx_pubchem (sid text, cid text, dtxsid text);
--     copy dtx_pubchem from '/opt/akokai/data/EPA/PubChem_DTXSID_mapping_file.txt'
--     with (format csv, delimiter '\t', header);

-- -- Find CASRN and Name for each DTXSID in table of molecules 
-- select dtx_cas.casrn, dtx_cas.name
--     from chem
--     left outer join dtx_cas on dtx_cas.dtxsid = chem.dtxsid;

-- -- Find CID for each DTXSID in table of molecules
-- select dtx_pubchem.cid
--     from chem
--     left outer join dtx_pubchem on dtx_pubchem.dtxsid = chem.dtxsid;

-- Find CASRN, Name, CID and join with all other columns on DTXSID
select chem.dtxsid, dtx_pubchem.cid, dtx_cas.casrn, dtx_cas.name,
       chem.inchikey, chem.inchi, chem.molecule
    from chem
    left outer join dtx_pubchem on dtx_pubchem.dtxsid = chem.dtxsid
    left outer join dtx_cas on dtx_cas.dtxsid = chem.dtxsid;

-- -- Merge on InChIKey using inner join...
-- select chem.dtxsid, cids.cid, chem.inchikey, chem.inchi, chem.molecule
--     from chem, cids
--     where chem.inchikey = cids.inchikey;
