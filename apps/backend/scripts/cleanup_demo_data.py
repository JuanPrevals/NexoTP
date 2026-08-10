"""Elimina exclusivamente los registros demo conocidos de NexoTP.

Uso seguro (solo muestra):
    python -m apps.backend.scripts.cleanup_demo_data

Eliminacion confirmada:
    python -m apps.backend.scripts.cleanup_demo_data --confirm DELETE_DEMO_DATA
"""

import argparse

from apps.backend.app.legacy import (
    Conexion,
    Empresa,
    Institucion,
    Mensaje,
    Notificacion,
    Novedad,
    Oferta,
    Postulacion,
    Practica,
    ResenaEmpresa,
    SeguimientoPractica,
    SesionMentoria,
    Usuario,
    app,
    db,
)


DEMO_USER_EMAILS = {"demo@nexotp.cl", "joaquin@nexotp.cl", "jheimy@nexotp.cl"}
DEMO_COMPANY_EMAILS = {
    "empresa@nexotp.cl",
    "contafacil@nexotp.cl",
    "logisur@nexotp.cl",
}
DEMO_INSTITUTION_EMAILS = {"liceo@nexotp.cl"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpieza acotada de datos demo de NexoTP")
    parser.add_argument("--confirm", default="", help="Escribe DELETE_DEMO_DATA para ejecutar")
    args = parser.parse_args()

    with app.app_context():
        users = Usuario.query.filter(Usuario.email.in_(DEMO_USER_EMAILS)).all()
        companies = Empresa.query.filter(Empresa.email.in_(DEMO_COMPANY_EMAILS)).all()
        institutions = Institucion.query.filter(
            Institucion.admin_email.in_(DEMO_INSTITUTION_EMAILS)
        ).all()
        user_ids = [item.id for item in users]
        company_ids = [item.id for item in companies]
        institution_ids = [item.id for item in institutions]
        offers = Oferta.query.filter(Oferta.empresa_id.in_(company_ids)).all() if company_ids else []
        offer_ids = [item.id for item in offers]
        applications = (
            Postulacion.query.filter(
                (Postulacion.usuario_id.in_(user_ids)) | (Postulacion.oferta_id.in_(offer_ids))
            ).all()
            if user_ids or offer_ids
            else []
        )
        application_ids = [item.id for item in applications]

        print(f"Usuarios demo: {len(users)}")
        print(f"Empresas demo: {len(companies)}")
        print(f"Instituciones demo: {len(institutions)}")
        print(f"Ofertas demo: {len(offers)}")
        print(f"Postulaciones relacionadas: {len(applications)}")
        if args.confirm != "DELETE_DEMO_DATA":
            print("Vista previa: no se elimino nada.")
            return

        practices = Practica.query.filter(Practica.postulacion_id.in_(application_ids)).all() if application_ids else []
        practice_ids = [item.id for item in practices]
        if practice_ids:
            SeguimientoPractica.query.filter(SeguimientoPractica.practica_id.in_(practice_ids)).delete(synchronize_session=False)
        if application_ids:
            Mensaje.query.filter(Mensaje.postulacion_id.in_(application_ids)).delete(synchronize_session=False)
            SesionMentoria.query.filter(SesionMentoria.postulacion_id.in_(application_ids)).delete(synchronize_session=False)
            Practica.query.filter(Practica.postulacion_id.in_(application_ids)).delete(synchronize_session=False)
            Postulacion.query.filter(Postulacion.id.in_(application_ids)).delete(synchronize_session=False)
        if user_ids:
            Conexion.query.filter((Conexion.usuario_id.in_(user_ids)) | (Conexion.colega_id.in_(user_ids))).delete(synchronize_session=False)
            Notificacion.query.filter(Notificacion.usuario_id.in_(user_ids)).delete(synchronize_session=False)
            ResenaEmpresa.query.filter(ResenaEmpresa.usuario_id.in_(user_ids)).delete(synchronize_session=False)
        if user_ids or company_ids or offer_ids:
            Novedad.query.filter(
                (Novedad.usuario_id.in_(user_ids))
                | (Novedad.empresa_id.in_(company_ids))
                | (Novedad.oferta_id.in_(offer_ids))
            ).delete(synchronize_session=False)
        if company_ids:
            ResenaEmpresa.query.filter(ResenaEmpresa.empresa_id.in_(company_ids)).delete(synchronize_session=False)
        if offer_ids:
            Oferta.query.filter(Oferta.id.in_(offer_ids)).delete(synchronize_session=False)
        if institution_ids:
            Practica.query.filter(Practica.institucion_id.in_(institution_ids)).update(
                {Practica.institucion_id: None}, synchronize_session=False
            )
        Usuario.query.filter(Usuario.id.in_(user_ids)).delete(synchronize_session=False)
        Empresa.query.filter(Empresa.id.in_(company_ids)).delete(synchronize_session=False)
        Institucion.query.filter(Institucion.id.in_(institution_ids)).delete(synchronize_session=False)
        db.session.commit()
        print("Datos demo eliminados correctamente.")


if __name__ == "__main__":
    main()
