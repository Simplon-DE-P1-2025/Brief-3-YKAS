-- 03_audit_operations.sql
-- Audit DB-level pour la table public.operations (INSERT/UPDATE/DELETE)
-- Objectif: traçabilité + historisation + reconstitution

BEGIN;

-- 1) Table d'audit
CREATE TABLE IF NOT EXISTS public.audit_operations (
    audit_id     BIGSERIAL PRIMARY KEY,
    operation_id BIGINT,
    action       TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    changed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    changed_by   TEXT NOT NULL DEFAULT current_user,
    old_row      JSONB,
    new_row      JSONB
);

-- 2) Index utiles (lecture audit + filtres)
CREATE INDEX IF NOT EXISTS idx_audit_operations_operation_id
    ON public.audit_operations(operation_id);

CREATE INDEX IF NOT EXISTS idx_audit_operations_changed_at
    ON public.audit_operations(changed_at);

-- 3) Fonction trigger
CREATE OR REPLACE FUNCTION public.fn_audit_operations()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO public.audit_operations(operation_id, action, old_row, new_row)
        VALUES (NEW.operation_id, 'INSERT', NULL, to_jsonb(NEW));
        RETURN NEW;

    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO public.audit_operations(operation_id, action, old_row, new_row)
        VALUES (NEW.operation_id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;

    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO public.audit_operations(operation_id, action, old_row, new_row)
        VALUES (OLD.operation_id, 'DELETE', to_jsonb(OLD), NULL);
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 4) Triggers (on drop si existent pour éviter doublons)
DROP TRIGGER IF EXISTS trg_audit_operations_ins ON public.operations;
DROP TRIGGER IF EXISTS trg_audit_operations_upd ON public.operations;
DROP TRIGGER IF EXISTS trg_audit_operations_del ON public.operations;

CREATE TRIGGER trg_audit_operations_ins
AFTER INSERT ON public.operations
FOR EACH ROW EXECUTE FUNCTION public.fn_audit_operations();

CREATE TRIGGER trg_audit_operations_upd
AFTER UPDATE ON public.operations
FOR EACH ROW EXECUTE FUNCTION public.fn_audit_operations();

CREATE TRIGGER trg_audit_operations_del
AFTER DELETE ON public.operations
FOR EACH ROW EXECUTE FUNCTION public.fn_audit_operations();

COMMIT;
