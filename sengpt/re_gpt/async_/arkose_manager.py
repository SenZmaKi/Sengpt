from ..errors import BackendError, RetryError
from curl_cffi.requests.session import AsyncSession, asyncio
from ..arkose_manager_utils import ArkoseManagerUtils
from ..utils import RELEASES_ENDPOINT


# TODO: Properly support Mac
class ArkoseManager(ArkoseManagerUtils):
    @staticmethod
    async def generate_arkose_token(session: AsyncSession) -> str | None:
        try:
            if not ArkoseManagerUtils.arkose_dll:
                await ArkoseManager.setup_binary(session)
            return ArkoseManagerUtils.get_arkose_token()
        except Exception as _:
            return await ArkoseManager.get_arkose_token_from_backup(session)

    @staticmethod
    async def get_arkose_token_from_backup(
        session: AsyncSession,
    ) -> str | None:
        for _ in range(5):
            response = await session.get(ArkoseManagerUtils.backup_token_generator_url)
            if response.text == "null":
                raise BackendError(error_code=505)
            try:
                return response.json()["token"]
            except Exception as _:
                await asyncio.sleep(0.7)
        raise RetryError(ArkoseManagerUtils.backup_token_generator_url)

    @staticmethod
    async def setup_binary(session: AsyncSession) -> None:
        ArkoseManager.prepare_binary_folder()
        response = await session.get(RELEASES_ENDPOINT)
        download_url = ArkoseManagerUtils.get_binary_download_url(response.json())
        if download_url:
            await ArkoseManager.download_binary(session, download_url)

    @staticmethod
    async def download_binary(session: AsyncSession, download_file_url: str):
        with open(ArkoseManagerUtils.binary_file_path, "wb") as output_file:
            if isinstance(session, AsyncSession):
                await session.get(
                    url=download_file_url,
                    content_callback=lambda chunk: output_file.write(chunk),
                )
            else:
                session.get(
                    url=download_file_url,
                    content_callback=lambda chunk: output_file.write(chunk),
                )

