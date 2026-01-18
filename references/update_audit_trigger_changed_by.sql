-- Remplacement de la fonction trigger + recréation des triggers
-- Normalisation : changed_by = lower(current_user)

BEGIN;

CREATE OR REPLACE FUNCTION public.fn_audit_operations()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO public.audit_operations(
            operation_id,
            action,
            changed_by,
            old_row,
            new_row
        )
        VALUES (
            NEW.operation_id,
            'INSERT',
            lower(current_user),
            NULL,
            to_jsonb(NEW)
        );
        RETURN NEW;

    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO public.audit_operations(
            operation_id,
            action,
            changed_by,
            old_row,
            new_row
        )
        VALUES (
            NEW.operation_id,
            'UPDATE',
            lower(current_user),
            to_jsonb(OLD),
            to_jsonb(NEW)
        );
        RETURN NEW;

    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO public.audit_operations(
            operation_id,
            action,
            changed_by,
            old_row,
            new_row
        )
        VALUES (
            OLD.operation_id,
            'DELETE',
            lower(current_user),
            to_jsonb(OLD),
            NULL
        );
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Triggers (drop/recreate pour être sûr qu'ils pointent bien sur la bonne fonction)
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
