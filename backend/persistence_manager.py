import json
import os
from datetime import datetime

MASTER_STORE = "backend/glossary_master.json"
_SS_MASTER_KEY = "_wm_master_store"  # Shared session_state key with WorkflowManager


class PersistenceManager:
    """
    Manages the persistent storage and versioning of approved glossary terms.
    Implements Granular SCD Type 2 (Term-Level Versioning).
    """

    @staticmethod
    def _load_store():
        """Load master store, using session_state as primary cache."""
        try:
            import streamlit as st
            if _SS_MASTER_KEY in st.session_state:
                return dict(st.session_state[_SS_MASTER_KEY])
        except Exception:
            pass
        if not os.path.exists(MASTER_STORE):
            return {}
        try:
            with open(MASTER_STORE, 'r') as f:
                data = json.load(f)
            try:
                import streamlit as st
                st.session_state[_SS_MASTER_KEY] = data
            except Exception:
                pass
            return data
        except Exception:
            return {}

    @staticmethod
    def _save_store(data):
        """Save master store to session_state and disk."""
        try:
            import streamlit as st
            st.session_state[_SS_MASTER_KEY] = data
        except Exception:
            pass
        os.makedirs(os.path.dirname(MASTER_STORE), exist_ok=True)
        try:
            with open(MASTER_STORE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass  # session_state still has data

    @classmethod
    def get_all_versions(cls, asset_guids):
        """
        Retrieves ALL versioned records for a list of asset GUIDs.
        Data is already flattened and decorated with Version/Active during storage.
        """
        store = cls._load_store()
        all_data = []
        found = False
        
        for guid in asset_guids:
            if guid in store:
                for record in store[guid]:
                    # Strict validation: Only return records that have the core business identifier
                    if isinstance(record, dict) and (record.get("Physical Term") or record.get("Business Term") or record.get("Glossary Term")):
                        all_data.append(record)
                        found = True
        
        return all_data if found else None

    @classmethod
    def get_all_stored_summaries(cls):
        """
        Returns a list of summaries for all assets in the master store.
        """
        store = cls._load_store()
        summaries = []
        
        for guid, records in store.items():
            if not records: continue
            
            # Find the most recent update
            sorted_records = sorted(records, key=lambda x: x.get("Stored At", ""), reverse=True)
            latest = sorted_records[0]
            
            # Count active records
            active_count = sum(1 for r in records if r.get("Active") == 1)
            
            table_name = latest.get("table_name", latest.get("Original Name", "Unknown Asset"))
            
            summaries.append({
                "Asset GUID": guid,
                "Asset Name": table_name,
                "Active Terms": active_count,
                "Total History": len(records),
                "Last Updated": latest.get("Stored At", "N/A"),
                "Version": latest.get("Version", 1)  # Fixed: Added Version key
            })
            
        return summaries

    @classmethod
    def get_dashboard_metrics(cls):
        """
        Aggregates global metrics for the Executive Dashboard.
        Ensures active terms are unique per asset.
        """
        store = cls._load_store()
        total_assets = len(store)
        total_active_terms = 0
        total_history_records = 0
        
        for records in store.values():
            total_history_records += len(records)
            active_ids = set()
            for r in records:
                if r.get("Active") == 1:
                    t_id = r.get("entity_guid") or r.get("Physical Term") or r.get("Original Name")
                    if t_id and t_id not in active_ids:
                        active_ids.add(t_id)
                        total_active_terms += 1
            
        return {
            "Total Assets": total_assets,
            "Active Terms": total_active_terms,
            "Total History": total_history_records
        }

    @classmethod
    def has_stored_data(cls, asset_guids):
        store = cls._load_store()
        return any(guid in store for guid in asset_guids)

    @classmethod
    def save_master_glossary(cls, selected_df):
        """
        Saves individual rows to the Master Store with SCD Type 2 logic.
        Each row is versioned independently based on its entity_guid or name.
        """
        if selected_df is None or selected_df.empty:
            return
            
        store = cls._load_store()
        timestamp = datetime.now().isoformat()
        
        # Group incoming rows by their parent table_guid
        for _, row in selected_df.iterrows():
            t_guid = row.get('table_guid')
            if not t_guid: continue
            
            if t_guid not in store:
                store[t_guid] = []
            
            # Identifier for the specific Term (Row)
            # Use entity_guid if available, fall back to Physical Term / Original Name
            row_id_key = row.get('entity_guid') or row.get('Physical Term') or row.get('Original Name')
            
            # SCD2 Logic: Find previous active record for THIS ROW
            for existing_record in store[t_guid]:
                if existing_record.get("Active") == 1:
                    existing_id = existing_record.get("entity_guid") or existing_record.get("Physical Term") or existing_record.get("Original Name")
                    if existing_id == row_id_key:
                        existing_record["Active"] = 0
            
            # Calculate next version for THIS ROW
            row_history = [r for r in store[t_guid] if (r.get("entity_guid") or r.get("Physical Term") or r.get("Original Name")) == row_id_key]
            next_version = len(row_history) + 1
            
            # Prepare new record
            new_record = row.to_dict()
            new_record["Version"] = next_version
            new_record["Active"] = 1
            new_record["Stored At"] = timestamp
            
            store[t_guid].append(new_record)
            
        cls._save_store(store)
        return True

    @classmethod
    def delete_record(cls, table_guid, row_id_key, version=None):
        """
        Deletes a specific record or all versions of a term.
        row_id_key is the entity_guid or Physical Term.
        """
        store = cls._load_store()
        if table_guid not in store:
            return False
            
        initial_count = len(store[table_guid])
        if version is not None:
            # Delete one specific version
            store[table_guid] = [
                r for r in store[table_guid] 
                if not ((r.get("entity_guid") or r.get("Original Name") or r.get("Physical Term")) == row_id_key and r.get("Version") == version)
            ]
        else:
            # Delete all versions of this specific term
            store[table_guid] = [
                r for r in store[table_guid] 
                if (r.get("entity_guid") or r.get("Original Name") or r.get("Physical Term")) != row_id_key
            ]
            
        if len(store[table_guid]) == 0:
            del store[table_guid]
            
        cls._save_store(store)
        return len(store.get(table_guid, [])) < initial_count or table_guid not in store
